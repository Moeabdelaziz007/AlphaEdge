from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol


@dataclass(slots=True)
class UsageQuota:
    """Per-tenant quota limits and current consumption."""

    daily_requests_limit: int = 10_000
    monthly_cost_limit_usd: float = 100.0
    concurrent_jobs_limit: int = 10

    daily_requests_used: int = 0
    monthly_cost_used_usd: float = 0.0
    concurrent_jobs_used: int = 0

    def can_consume(self, requests: int = 0, cost_usd: float = 0.0, concurrent_jobs: int = 0) -> bool:
        return (
            self.daily_requests_used + requests <= self.daily_requests_limit
            and self.monthly_cost_used_usd + cost_usd <= self.monthly_cost_limit_usd
            and self.concurrent_jobs_used + concurrent_jobs <= self.concurrent_jobs_limit
        )

    def consume(self, requests: int = 0, cost_usd: float = 0.0, concurrent_jobs: int = 0) -> None:
        self.daily_requests_used += requests
        self.monthly_cost_used_usd += cost_usd
        self.concurrent_jobs_used += concurrent_jobs


@dataclass(slots=True)
class TenantRecord:
    tenant_id: str
    name: str
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    api_key_hashes: List[str] = field(default_factory=list)
    quotas: UsageQuota = field(default_factory=UsageQuota)


class TenantRegistry:
    """Tenant registry with API-key management and quota tracking."""

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantRecord] = {}

    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def register_tenant(self, tenant_id: str, name: str, quotas: Optional[UsageQuota] = None) -> str:
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant '{tenant_id}' already exists")

        record = TenantRecord(tenant_id=tenant_id, name=name, quotas=quotas or UsageQuota())
        api_key = self.issue_api_key(tenant_id, bootstrap_record=record)
        self._tenants[tenant_id] = record
        return api_key

    def issue_api_key(self, tenant_id: str, bootstrap_record: Optional[TenantRecord] = None) -> str:
        tenant = bootstrap_record or self.get_tenant(tenant_id)
        raw_key = f"ae_{tenant_id}_{secrets.token_urlsafe(24)}"
        tenant.api_key_hashes.append(self._hash_api_key(raw_key))
        return raw_key

    def authenticate(self, tenant_id: str, api_key: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            return False
        return self._hash_api_key(api_key) in tenant.api_key_hashes

    def get_tenant(self, tenant_id: str) -> TenantRecord:
        if tenant_id not in self._tenants:
            raise KeyError(f"Unknown tenant '{tenant_id}'")
        return self._tenants[tenant_id]

    def consume_quota(self, tenant_id: str, requests: int = 0, cost_usd: float = 0.0, concurrent_jobs: int = 0) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant.quotas.can_consume(requests=requests, cost_usd=cost_usd, concurrent_jobs=concurrent_jobs):
            return False
        tenant.quotas.consume(requests=requests, cost_usd=cost_usd, concurrent_jobs=concurrent_jobs)
        return True


@dataclass(slots=True)
class MeteringEvent:
    service: str
    tenant_id: str
    metric: str
    value: float
    unit: str
    timestamp: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class MeteringEventBus:
    """Unified event bus that all generator services publish metering events to."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[MeteringEvent], None]] = []
        self._events: List[MeteringEvent] = []

    def publish(self, event: MeteringEvent) -> None:
        self._events.append(event)
        for subscriber in self._subscribers:
            subscriber(event)

    def subscribe(self, handler: Callable[[MeteringEvent], None]) -> None:
        self._subscribers.append(handler)

    def events(self, tenant_id: Optional[str] = None) -> List[MeteringEvent]:
        if tenant_id is None:
            return list(self._events)
        return [event for event in self._events if event.tenant_id == tenant_id]


class BillingProvider(Protocol):
    def record_usage(self, event: MeteringEvent) -> float: ...

    def get_monthly_cost(self, tenant_id: str) -> float: ...


class MockBillingProvider:
    """Simple in-memory billing adapter for initial integration."""

    def __init__(self, metric_prices: Optional[Dict[str, float]] = None) -> None:
        self._metric_prices = metric_prices or {
            "tokens": 0.000002,
            "images": 0.02,
            "audio_seconds": 0.0005,
            "requests": 0.0001,
        }
        self._costs_by_tenant: Dict[str, float] = {}

    def record_usage(self, event: MeteringEvent) -> float:
        price_per_unit = self._metric_prices.get(event.metric, 0.0)
        event_cost = event.value * price_per_unit
        self._costs_by_tenant[event.tenant_id] = self._costs_by_tenant.get(event.tenant_id, 0.0) + event_cost
        return event_cost

    def get_monthly_cost(self, tenant_id: str) -> float:
        return round(self._costs_by_tenant.get(tenant_id, 0.0), 6)


@dataclass(slots=True)
class TenantPolicy:
    max_cpu_cores: int = 4
    max_memory_gb: int = 8
    max_gpu_count: int = 0
    allow_background_jobs: bool = True


class PolicyEngine:
    """Policy engine to enforce per-tenant resource limits."""

    def __init__(self) -> None:
        self._policies: Dict[str, TenantPolicy] = {}

    def set_policy(self, tenant_id: str, policy: TenantPolicy) -> None:
        self._policies[tenant_id] = policy

    def get_policy(self, tenant_id: str) -> TenantPolicy:
        return self._policies.get(tenant_id, TenantPolicy())

    def is_allocation_allowed(
        self,
        tenant_id: str,
        cpu_cores: int,
        memory_gb: int,
        gpu_count: int,
        background_job: bool,
    ) -> bool:
        policy = self.get_policy(tenant_id)
        if background_job and not policy.allow_background_jobs:
            return False
        return (
            cpu_cores <= policy.max_cpu_cores
            and memory_gb <= policy.max_memory_gb
            and gpu_count <= policy.max_gpu_count
        )


class DashboardAPI:
    """Unified API facade for operations, health, and cost reporting."""

    def __init__(
        self,
        registry: TenantRegistry,
        metering_bus: MeteringEventBus,
        billing_provider: BillingProvider,
        policy_engine: PolicyEngine,
    ) -> None:
        self.registry = registry
        self.metering_bus = metering_bus
        self.billing_provider = billing_provider
        self.policy_engine = policy_engine

    def get_operations_summary(self, tenant_id: str) -> Dict[str, Any]:
        tenant = self.registry.get_tenant(tenant_id)
        events = self.metering_bus.events(tenant_id=tenant_id)
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "total_events": len(events),
            "api_keys_active": len(tenant.api_key_hashes),
            "quota": {
                "daily_requests": f"{tenant.quotas.daily_requests_used}/{tenant.quotas.daily_requests_limit}",
                "monthly_cost_usd": f"{tenant.quotas.monthly_cost_used_usd:.4f}/{tenant.quotas.monthly_cost_limit_usd:.4f}",
                "concurrent_jobs": f"{tenant.quotas.concurrent_jobs_used}/{tenant.quotas.concurrent_jobs_limit}",
            },
        }

    def get_health_summary(self, tenant_id: str) -> Dict[str, Any]:
        quota = self.registry.get_tenant(tenant_id).quotas
        policy = self.policy_engine.get_policy(tenant_id)

        requests_ratio = quota.daily_requests_used / quota.daily_requests_limit if quota.daily_requests_limit else 1.0
        cost_ratio = quota.monthly_cost_used_usd / quota.monthly_cost_limit_usd if quota.monthly_cost_limit_usd else 1.0

        status = "healthy"
        if requests_ratio > 0.9 or cost_ratio > 0.9:
            status = "warning"
        if requests_ratio >= 1.0 or cost_ratio >= 1.0:
            status = "throttled"

        return {
            "tenant_id": tenant_id,
            "status": status,
            "request_usage_ratio": round(requests_ratio, 4),
            "cost_usage_ratio": round(cost_ratio, 4),
            "policy": {
                "max_cpu_cores": policy.max_cpu_cores,
                "max_memory_gb": policy.max_memory_gb,
                "max_gpu_count": policy.max_gpu_count,
                "allow_background_jobs": policy.allow_background_jobs,
            },
        }

    def get_cost_summary(self, tenant_id: str) -> Dict[str, Any]:
        return {
            "tenant_id": tenant_id,
            "estimated_monthly_cost_usd": self.billing_provider.get_monthly_cost(tenant_id),
            "metered_events": len(self.metering_bus.events(tenant_id=tenant_id)),
        }


class ControlPlane:
    """Composition root for the control-plane layer."""

    def __init__(self, billing_provider: Optional[BillingProvider] = None) -> None:
        self.registry = TenantRegistry()
        self.metering_bus = MeteringEventBus()
        self.billing = billing_provider or MockBillingProvider()
        self.policy = PolicyEngine()
        self.dashboard = DashboardAPI(
            registry=self.registry,
            metering_bus=self.metering_bus,
            billing_provider=self.billing,
            policy_engine=self.policy,
        )


    def meter_usage(
        self,
        service: str,
        tenant_id: str,
        metric: str,
        value: float,
        unit: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        event = MeteringEvent(
            service=service,
            tenant_id=tenant_id,
            metric=metric,
            value=value,
            unit=unit,
            metadata=metadata or {},
        )
        event_cost = self.billing.record_usage(event)
        self.metering_bus.publish(event)
        return self.registry.consume_quota(tenant_id=tenant_id, requests=1, cost_usd=event_cost)
