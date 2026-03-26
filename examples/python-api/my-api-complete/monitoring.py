import time
import logging
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RestaurantOrderAPI')

# Create Flask app
app = Flask('RestaurantOrderAPI')

# Custom Prometheus metrics
# Counter for total orders
ORDER_COUNT = Counter('restaurant_orders_total', 'Total number of orders received', ['status'])

# Histogram for order processing duration
ORDER_PROCESSING_DURATION = Histogram(
    'restaurant_order_processing_duration_seconds',
    'Order processing duration in seconds',
    ['endpoint']
)

# Gauge for current active orders
ACTIVE_ORDERS = Gauge('restaurant_active_orders', 'Number of currently active orders')

# Counter for menu requests
MENU_REQUESTS = Counter('restaurant_menu_requests_total', 'Total number of menu requests')

# Histogram for API response times
API_RESPONSE_TIME = Histogram(
    'restaurant_api_response_time_seconds',
    'API response time in seconds',
    ['method', 'endpoint', 'status']
)

# Gauge for service health status (1=healthy, 0=unhealthy)
HEALTH_STATUS = Gauge('restaurant_service_health', 'Service health status')

# Counter for payment processing
PAYMENT_PROCESSED = Counter('restaurant_payments_total', 'Total number of payments processed', ['status'])

# Alerting rules (represented as functions that could trigger alerts)
ALERT_RULES = {
    'HighOrderFailureRate': {
        'expr': 'rate(restaurant_orders_total{status="failed"}[5m]) / rate(restaurant_orders_total[5m]) > 0.1',
        'for': '5m',
        'labels': {'severity': 'critical'},
        'annotations': {
            'summary': 'High order failure rate',
            'description': 'More than 10% of orders are failing in the last 5 minutes.'
        }
    },
    'HighLatency': {
        'expr': 'rate(restaurant_order_processing_duration_seconds_sum[5m]) / rate(restaurant_order_processing_duration_seconds_count[5m]) > 2',
        'for': '10m',
        'labels': {'severity': 'warning'},
        'annotations': {
            'summary': 'High order processing latency',
            'description': 'Average order processing time exceeds 2 seconds for the last 10 minutes.'
        }
    },
    'ServiceDown': {
        'expr': 'restaurant_service_health == 0',
        'for': '1m',
        'labels': {'severity': 'critical'},
        'annotations': {
            'summary': 'RestaurantOrderAPI is unhealthy',
            'description': 'The service health check has been failing for more than 1 minute.'
        }
    }
}

# Simulated menu data
MENU = {
    "items": [
        {"id": 1, "name": "Pizza", "price": 12.99},
        {"id": 2, "name": "Burger", "price": 9.99},
        {"id": 3, "name": "Pasta", "price": 11.50},
        {"id": 4, "name": "Salad", "price": 7.99}
    ]
}

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Calculate response time
    if hasattr(request, 'start_time'):
        response_time = time.time() - request.start_time
        API_RESPONSE_TIME.labels(
            method=request.method,
            endpoint=request.endpoint or request.path,
            status=response.status_code
        ).observe(response_time)
    
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Simulate health check logic
        is_healthy = True  # In real app, check DB connections, external services, etc.
        
        if is_healthy:
            HEALTH_STATUS.set(1)
            logger.info("Health check passed")
            return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200
        else:
            HEALTH_STATUS.set(0)
            logger.error("Health check failed")
            return jsonify({"status": "unhealthy", "timestamp": datetime.utcnow().isoformat()}), 503
            
    except Exception as e:
        HEALTH_STATUS.set(0)
        logger.error(f"Health check exception: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}), 503

@app.route('/metrics', methods=['GET'])
def metrics():
    """Exposes Prometheus metrics"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/menu', methods=['GET'])
def get_menu():
    """Get restaurant menu"""
    try:
        MENU_REQUESTS.inc()
        logger.info("Menu requested by client", extra={
            'client_ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        })
        
        return jsonify(MENU), 200
        
    except Exception as e:
        logger.error(f"Error retrieving menu: {str(e)}")
        return jsonify({"error": "Failed to retrieve menu"}), 500

@app.route('/order', methods=['POST'])
def create_order():
    """Create a new order"""
    order_id = f"ORD{int(time.time())}"
    
    try:
        # Increment active orders gauge
        ACTIVE_ORDERS.inc()
        
        # Log order request
        logger.info("Order received", extra={
            'order_id': order_id,
            'client_ip': request.remote_addr,
            'payload': request.get_json()
        })
        
        with ORDER_PROCESSING_DURATION.labels(endpoint='/order').time():
            # Simulate order processing
            time.sleep(0.1)  # Simulate processing delay
            
            order_data = request.get_json()
            if not order_data or 'items' not in order_data:
                logger.warning("Invalid order format", extra={'order_id': order_id})
                ORDER_COUNT.labels(status='invalid').inc()
                return jsonify({"error": "Invalid order format"}), 400
            
            # Simulate payment processing
            payment_success = True  # In real app, integrate with payment gateway
            if payment_success:
                PAYMENT_PROCESSED.labels(status='success').inc()
                logger.info("Order processed successfully", extra={
                    'order_id': order_id,
                    'total_items': len(order_data['items'])
                })
                ORDER_COUNT.labels(status='success').inc()
                response = {
                    "order_id": order_id,
                    "status": "confirmed",
                    "estimated_delivery": (datetime.utcnow().timestamp() + 1800)  # 30 minutes
                }
                return jsonify(response), 201
            else:
                PAYMENT_PROCESSED.labels(status='failed').inc()
                logger.error("Payment failed", extra={'order_id': order_id})
                ORDER_COUNT.labels(status='failed').inc()
                return jsonify({"error": "Payment failed"}), 402
                
    except Exception as e:
        logger.error(f"Order processing failed: {str(e)}", extra={'order_id': order_id})
        ORDER_COUNT.labels(status='error').inc()
        return jsonify({"error": "Order processing failed"}), 500
        
    finally:
        # Decrement active orders gauge
        ACTIVE_ORDERS.dec()

@app.route('/order/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """Get order status"""
    try:
        logger.info("Order status requested", extra={
            'order_id': order_id,
            'client_ip': request.remote_addr
        })
        
        # Simulate order lookup
        time.sleep(0.05)
        
        # Simulate order status
        status = "delivered" if "delivered" in order_id.lower() else "preparing"
        
        return jsonify({
            "order_id": order_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving order status for {order_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve order status"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning("Endpoint not found", extra={
        'path': request.path,
        'method': request.method,
        'client_ip': request.remote_addr
    })
    API_RESPONSE_TIME.labels(
        method=request.method,
        endpoint=request.path,
        status=404
    ).observe(time.time() - getattr(request, 'start_time', time.time()))
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error", extra={
        'path': request.path,
        'method': request.method,
        'client_ip': request.remote_addr,
        'error': str(error)
    })
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Set initial health status
    HEALTH_STATUS.set(1)
    logger.info("RestaurantOrderAPI starting with monitoring enabled")
    app.run(host='0.0.0.0', port=5000, debug=False)