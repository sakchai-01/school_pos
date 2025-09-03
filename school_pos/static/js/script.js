// Global variables
let cart = [];
let currentShopId = null;

// DOM Elements
const cartCount = document.querySelector('.cart-count');
const cartModal = document.getElementById('cartModal');
const loadingSpinner = document.querySelector('.loading');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadCartFromSession();
    setupEventListeners();
});

function initializeApp() {
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .shop-card, .menu-item').forEach(el => {
        observer.observe(el);
    });
}

function setupEventListeners() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', handleAddToCart);
    });

    // Quantity controls
    document.querySelectorAll('.quantity-plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            input.value = parseInt(input.value) + 1;
        });
    });

    document.querySelectorAll('.quantity-minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.nextElementSibling;
            if (parseInt(input.value) > 1) {
                input.value = parseInt(input.value) - 1;
            }
        });
    });

    // Toggle availability switches
    document.querySelectorAll('.availability-toggle').forEach(toggle => {
        toggle.addEventListener('change', handleAvailabilityToggle);
    });

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', validateForm);
    });

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }
}

async function handleAddToCart(event) {
    const btn = event.target;
    const originalText = btn.textContent;
    
    // Show loading
    btn.innerHTML = '<span class="loading"></span> กำลังเพิ่ม...';
    btn.disabled = true;

    try {
        const itemId = btn.dataset.itemId;
        const itemName = btn.dataset.itemName;
        const itemPrice = parseFloat(btn.dataset.itemPrice);
        const shopId = btn.dataset.shopId;
        
        // Get quantity
        const quantityInput = btn.closest('.menu-item').querySelector('.quantity-input');
        const quantity = parseInt(quantityInput ? quantityInput.value : 1);

        const response = await fetch('/add_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: itemId,
                name: itemName,
                price: itemPrice,
                quantity: quantity,
                shop_id: shopId
            })
        });

        const result = await response.json();

        if (result.success) {
            // Update cart count
            updateCartCount(result.cart_count);
            
            // Show success animation
            btn.innerHTML = '<span class="success-checkmark"></span> เพิ่มแล้ว!';
            btn.classList.add('btn-success');
            
            // Show notification
            showNotification('เพิ่มสินค้าลงตะกร้าเรียบร้อย!', 'success');
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('btn-success');
                btn.disabled = false;
            }, 2000);
        }
    } catch (error) {
        console.error('Error adding to cart:', error);
        showNotification('เกิดข้อผิดพลาด กรุณาลองใหม่', 'error');
        
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function handleAvailabilityToggle(event) {
    const toggle = event.target;
    const itemId = toggle.dataset.itemId;
    const available = toggle.checked;

    try {
        const response = await fetch('/toggle_availability', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: itemId,
                available: available
            })
        });

        const result = await response.json();
        
        if (result.success) {
            const statusSpan = toggle.closest('tr').querySelector('.status-indicator');
            if (statusSpan) {
                statusSpan.textContent = available ? 'มีจำหน่าย' : 'หมด';
                statusSpan.className = available ? 'status-available' : 'status-unavailable';
            }
            
            showNotification(
                available ? 'เปิดจำหน่ายแล้ว' : 'ปิดจำหน่ายแล้ว', 
                'success'
            );
        }
    } catch (error) {
        console.error('Error toggling availability:', error);
        toggle.checked = !available; // Revert toggle
        showNotification('เกิดข้อผิดพลาด กรุณาลองใหม่', 'error');
    }
}

function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    const items = document.querySelectorAll('.menu-item, .shop-card');
    
    items.forEach(item => {
        const name = item.querySelector('.menu-name, .shop-name').textContent.toLowerCase();
        
        if (name.includes(searchTerm)) {
            item.style.display = 'block';
            item.classList.add('fade-in');
        } else {
            item.style.display = 'none';
            item.classList.remove('fade-in');
        }
    });
}

function validateForm(event) {
    const form = event.target;
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        const value = input.value.trim();
        const errorMsg = input.nextElementSibling;
        
        // Remove existing error styling
        input.classList.remove('error');
        if (errorMsg && errorMsg.classList.contains('error-message')) {
            errorMsg.remove();
        }
        
        if (!value) {
            isValid = false;
            input.classList.add('error');
            
            const error = document.createElement('div');
            error.classList.add('error-message');
            error.textContent = 'กรุณาใส่ข้อมูลในช่องนี้';
            error.style.color = 'var(--accent-color)';
            error.style.fontSize = '0.8rem';
            error.style.marginTop = '0.25rem';
            
            input.parentNode.insertBefore(error, input.nextSibling);
        }
        
        // Specific validation for different input types
        if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                input.classList.add('error');
                
                const error = document.createElement('div');
                error.classList.add('error-message');
                error.textContent = 'รูปแบบอีเมลไม่ถูกต้อง';
                error.style.color = 'var(--accent-color)';
                error.style.fontSize = '0.8rem';
                error.style.marginTop = '0.25rem';
                
                input.parentNode.insertBefore(error, input.nextSibling);
            }
        }
        
        if (input.type === 'number' && value) {
            const numValue = parseFloat(value);
            if (isNaN(numValue) || numValue <= 0) {
                isValid = false;
                input.classList.add('error');
                
                const error = document.createElement('div');
                error.classList.add('error-message');
                error.textContent = 'กรุณาใส่ตัวเลขที่มากกว่า 0';
                error.style.color = 'var(--accent-color)';
                error.style.fontSize = '0.8rem';
                error.style.marginTop = '0.25rem';
                
                input.parentNode.insertBefore(error, input.nextSibling);
            }
        }
    });
    
    if (!isValid) {
        event.preventDefault();
        showNotification('กรุณาใส่ข้อมูลให้ครบถ้วน', 'error');
    }
}

function updateCartCount(count) {
    if (cartCount) {
        cartCount.textContent = count;
        cartCount.style.display = count > 0 ? 'flex' : 'none';
    }
}

function loadCartFromSession() {
    // This would be implemented to sync with server session
    // For now, we'll use localStorage as backup
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
        updateCartCount(cart.length);
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.classList.add('notification', `notification-${type}`);
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Add styles
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        backgroundColor: type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff',
        color: 'white',
        padding: '1rem 1.5rem',
        borderRadius: 'var(--border-radius)',
        boxShadow: 'var(--shadow)',
        zIndex: '1001',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        minWidth: '300px'
    });
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        closeNotification(notification);
    });
    
    // Auto close after 5 seconds
    setTimeout(() => {
        closeNotification(notification);
    }, 5000);
}

function closeNotification(notification) {
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// Shop selection modal
function openShopModal() {
    const modal = document.getElementById('shopModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeShopModal() {
    const modal = document.getElementById('shopModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Cart functions
function openCart() {
    window.location.href = '/cart';
}

function updateItemQuantity(itemId, quantity) {
    if (quantity <= 0) {
        removeFromCart(itemId);
        return;
    }
    
    // Update cart item quantity
    cart.forEach(item => {
        if (item.item_id === itemId) {
            item.quantity = quantity;
        }
    });
    
    // Update display
    updateCartDisplay();
    localStorage.setItem('cart', JSON.stringify(cart));
}

function removeFromCart(itemId) {
    cart = cart.filter(item => item.item_id !== itemId);
    updateCartDisplay();
    updateCartCount(cart.length);
    localStorage.setItem('cart', JSON.stringify(cart));
    showNotification('ลบสินค้าออกจากตะกร้าแล้ว', 'info');
}

function updateCartDisplay() {
    const cartItems = document.querySelector('.cart-items');
    const cartTotal = document.querySelector('.cart-total-amount');
    
    if (cartItems) {
        let total = 0;
        cartItems.innerHTML = '';
        
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            
            const cartItem = document.createElement('div');
            cartItem.classList.add('cart-item');
            cartItem.innerHTML = `
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>฿${item.price}</p>
                </div>
                <div class="cart-item-controls">
                    <button class="quantity-btn" onclick="updateItemQuantity('${item.item_id}', ${item.quantity - 1})">-</button>
                    <span class="quantity">${item.quantity}</span>
                    <button class="quantity-btn" onclick="updateItemQuantity('${item.item_id}', ${item.quantity + 1})">+</button>
                    <button class="remove-btn" onclick="removeFromCart('${item.item_id}')">&times;</button>
                </div>
                <div class="cart-item-total">฿${itemTotal}</div>
            `;
            
            cartItems.appendChild(cartItem);
        });
        
        if (cartTotal) {
            cartTotal.textContent = `฿${total}`;
        }
    }
}

// Print functions for shop owners
function printSalesReport() {
    window.print();
}

function exportToCSV() {
    // Implementation for CSV export
    const table = document.querySelector('.data-table table');
    if (!table) return;
    
    let csv = '';
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('th, td');
        const rowData = Array.from(cols).map(col => `"${col.textContent}"`).join(',');
        csv += rowData + '\n';
    });
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sales_report.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e);
    showNotification('เกิดข้อผิดพลาดในระบบ', 'error');
});

// Online/offline detection
window.addEventListener('online', function() {
    showNotification('เชื่อมต่ออินเทอร์เน็ตแล้ว', 'success');
});

window.addEventListener('offline', function() {
    showNotification('ไม่มีการเชื่อมต่ออินเทอร์เน็ต', 'warning');
});

// PWA support
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(function(registration) {
            console.log('SW registered: ', registration);
        })
        .catch(function(registrationError) {
            console.log('SW registration failed: ', registrationError);
        });
}