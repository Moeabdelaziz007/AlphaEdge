package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/stripe/stripe-go/v74"
	"github.com/stripe/stripe-go/v74/webhook"
)

// Aether Gateway: The Neural Financial Hub
func main() {
	stripe.Key = os.Getenv("STRIPE_SECRET_KEY")
	endpointSecret := os.Getenv("STRIPE_WEBHOOK_SECRET")

	router := gin.Default()

	// 1. JWT Issuance (Mock for now)
	router.POST("/v1/auth/token", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"token": "AGN_JWT_EYJ...",
			"expiry": "24h",
		})
	})

	// 2. Stripe Webhook Handler (Grounded in First Principles)
	router.POST("/webhooks/stripe", func(c *gin.Context) {
		payload, err := c.GetRawData()
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Payload missing"})
			return
		}

		sigHeader := c.GetHeader("Stripe-Signature")
		event, err := webhook.ConstructEvent(payload, sigHeader, endpointSecret)

		if err != nil {
			log.Printf("⚠️ Webhook Signature Validation Failed: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid signature"})
			return
		}

		// Neural Routing based on Event Type
		switch event.Type {
		case "checkout.session.completed":
			var session stripe.CheckoutSession
			err := json.Unmarshal(event.Data.Raw, &session)
			if err != nil {
				log.Printf("Error unmarshalling: %v", err)
				return
			}
			handleSuccessfulSubscription(session)
		case "customer.subscription.deleted":
			handleCancelledSubscription(event.Data.Object["id"].(string))
		default:
			fmt.Fprintf(os.Stderr, "Unhandled event type: %s\n", event.Type)
		}

		c.Status(http.StatusOK)
	})

	port := os.Getenv("AETHER_PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("🚀 Aether Gateway Active on Port %s", port)
	router.Run(":" + port)
}

func handleSuccessfulSubscription(session stripe.CheckoutSession) {
	log.Printf("💰 New Subscription: %s (Customer: %s)", session.ID, session.Customer.ID)
	// Code to update Neon DB via AlphaEdge Internal API would go here
}

func handleCancelledSubscription(subscriptionID string) {
	log.Printf("💔 Subscription Cancelled: %s", subscriptionID)
}
