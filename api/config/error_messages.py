"""Error and success message constants."""

# Error Messages
ERROR_MESSAGES = {
    # Authentication Errors
    "invalid_credentials": "Invalid email or password.",
    "account_locked": "Account temporarily locked due to too many failed login attempts.",
    "account_inactive": "Your account is currently inactive. Please contact support.",
    "email_not_verified": "Please verify your email address before logging in.",
    "password_expired": "Your password has expired. Please reset your password.",
    "session_expired": "Your session has expired. Please log in again.",
    "invalid_token": "Invalid or expired token.",
    "insufficient_permissions": "You don't have permission to perform this action.",
    # Product & Inventory Errors
    "product_not_found": "Product not found.",
    "insufficient_stock": "Insufficient stock for this product.",
    "product_unavailable": "This product is currently unavailable.",
    "invalid_quantity": "Please enter a valid quantity.",
    "max_quantity_exceeded": "Maximum quantity per order exceeded.",
    "variant_not_found": "Product variant not found.",
    # Cart & Checkout Errors
    "empty_cart": "Your cart is empty.",
    "cart_expired": "Your cart has expired. Please add items again.",
    "invalid_cart_item": "Invalid cart item.",
    "cart_limit_exceeded": "Cart item limit exceeded.",
    # Order Errors
    "order_not_found": "Order not found.",
    "order_cancelled": "This order has been cancelled.",
    "order_already_shipped": "This order has already been shipped.",
    "cannot_modify_order": "This order cannot be modified.",
    "invalid_order_status": "Invalid order status.",
    # Payment Errors
    "payment_failed": "Payment processing failed. Please try again.",
    "invalid_payment_method": "Invalid payment method.",
    "payment_declined": "Your payment was declined. Please check your payment details.",
    "insufficient_funds": "Insufficient funds. Please try a different payment method.",
    "payment_timeout": "Payment processing timed out. Please try again.",
    "refund_failed": "Refund processing failed. Please contact support.",
    # Shipping Errors
    "shipping_unavailable": "Shipping is not available to this address.",
    "invalid_shipping_address": "Please provide a valid shipping address.",
    "shipping_method_unavailable": "Selected shipping method is not available.",
    # Coupon & Discount Errors
    "invalid_coupon": "Invalid or expired coupon code.",
    "coupon_expired": "This coupon has expired.",
    "coupon_limit_exceeded": "Coupon usage limit exceeded.",
    "coupon_minimum_not_met": "Minimum order amount not met for this coupon.",
    "coupon_not_applicable": "This coupon is not applicable to your order.",
    # Loyalty Errors
    "insufficient_loyalty_points": "Insufficient loyalty points.",
    # User Account Errors
    "email_already_exists": "An account with this email already exists.",
    "username_already_exists": "This username is already taken.",
    "weak_password": "Password is too weak. Please choose a stronger password.",
    "password_mismatch": "Passwords do not match.",
    "invalid_email_format": "Please enter a valid email address.",
    "invalid_phone_number": "Please enter a valid phone number.",
    # Address Errors
    "invalid_address": "Please provide a valid address.",
    "address_not_found": "Address not found.",
    "default_address_required": "You must have at least one default address.",
    # File Upload Errors
    "file_too_large": "File size exceeds maximum allowed size.",
    "invalid_file_type": "Invalid file type. Please upload a supported file format.",
    "upload_failed": "File upload failed. Please try again.",
    # General Errors
    "server_error": "An internal server error occurred. Please try again later.",
    "network_error": "Network error. Please check your connection and try again.",
    "validation_error": "Please correct the errors below.",
    "rate_limit_exceeded": "Too many requests. Please try again later.",
    "service_unavailable": "Service temporarily unavailable. Please try again later.",
    "maintenance_mode": "System is currently under maintenance. Please try again later.",
    "invalid_request": "Invalid request format.",
    "resource_not_found": "Requested resource not found.",
}

# Success Messages
SUCCESS_MESSAGES = {
    # Authentication Success
    "login_successful": "Login successful.",
    "logout_successful": "You have been logged out successfully.",
    "account_created": "Account created successfully.",
    "email_verified": "Email address verified successfully.",
    "password_updated": "Password updated successfully.",
    "password_reset_sent": "Password reset instructions sent to your email.",
    "password_reset_successful": "Password reset successful.",
    # Profile & Account Success
    "profile_updated": "Profile updated successfully.",
    "address_added": "Address added successfully.",
    "address_updated": "Address updated successfully.",
    "address_deleted": "Address deleted successfully.",
    "preferences_saved": "Preferences saved successfully.",
    # Product & Inventory Success
    "product_added_to_cart": "Product added to cart successfully.",
    "cart_updated": "Cart updated successfully.",
    "product_removed_from_cart": "Product removed from cart.",
    "cart_cleared": "Cart cleared successfully.",
    "wishlist_updated": "Wishlist updated successfully.",
    # Order Success
    "order_placed": "Order placed successfully.",
    "order_updated": "Order updated successfully.",
    "order_cancelled": "Order cancelled successfully.",
    "order_shipped": "Order has been shipped.",
    "order_delivered": "Order has been delivered.",
    # Payment Success
    "payment_processed": "Payment processed successfully.",
    "refund_processed": "Refund has been processed.",
    "payment_method_added": "Payment method added successfully.",
    "payment_method_updated": "Payment method updated successfully.",
    "payment_method_removed": "Payment method removed successfully.",
    # Communication Success
    "email_sent": "Email sent successfully.",
    "feedback_submitted": "Feedback submitted successfully.",
    "review_submitted": "Review submitted successfully.",
    "newsletter_subscribed": "Successfully subscribed to newsletter.",
    "newsletter_unsubscribed": "Successfully unsubscribed from newsletter.",
    # Admin Success
    "settings_saved": "Settings saved successfully.",
    "data_exported": "Data exported successfully.",
    "data_imported": "Data imported successfully.",
    "cache_cleared": "Cache cleared successfully.",
    # File Upload Success
    "file_uploaded": "File uploaded successfully.",
    "image_processed": "Image processed successfully.",
    # General Success
    "operation_completed": "Operation completed successfully.",
    "data_saved": "Data saved successfully.",
    "changes_applied": "Changes applied successfully.",
}
