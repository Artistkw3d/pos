// ========================================
// 🔧 Fetch Helper مع Error Handling
// ========================================

/**
 * Fetch مع timeout و error handling محسّن
 */
async function safeFetch(url, options = {}, timeoutMs = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // تحقق من status
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        // تحديد نوع الخطأ
        if (error.name === 'AbortError') {
            throw new Error('انتهت مهلة الاتصال - الرجاء المحاولة مرة أخرى');
        }
        
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('لا يوجد اتصال بالإنترنت - الرجاء التحقق من الاتصال');
        }
        
        // خطأ آخر
        throw error;
    }
}

/**
 * عرض رسالة خطأ للمستخدم
 */
function showError(message, duration = 5000) {
    // إزالة الإشعارات القديمة
    const oldNotif = document.getElementById('errorNotification');
    if (oldNotif) oldNotif.remove();
    
    // إنشاء إشعار جديد
    const notification = document.createElement('div');
    notification.id = 'errorNotification';
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        left: 20px;
        max-width: 500px;
        margin: 0 auto;
        padding: 16px 24px;
        background: #dc3545;
        color: white;
        border-radius: 12px;
        font-weight: bold;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(220, 53, 69, 0.4);
        animation: slideInDown 0.3s ease;
        text-align: center;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
            <span style="font-size: 24px;">⚠️</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // إخفاء بعد المدة المحددة
    setTimeout(() => {
        notification.style.animation = 'slideOutUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * عرض رسالة نجاح
 */
function showSuccess(message, duration = 3000) {
    const oldNotif = document.getElementById('successNotification');
    if (oldNotif) oldNotif.remove();
    
    const notification = document.createElement('div');
    notification.id = 'successNotification';
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        left: 20px;
        max-width: 500px;
        margin: 0 auto;
        padding: 16px 24px;
        background: #28a745;
        color: white;
        border-radius: 12px;
        font-weight: bold;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(40, 167, 69, 0.4);
        animation: slideInDown 0.3s ease;
        text-align: center;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
            <span style="font-size: 24px;">✅</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// CSS للـ animations
const styleEl = document.createElement('style');
styleEl.textContent = `
@keyframes slideInDown {
    from {
        transform: translateY(-100px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes slideOutUp {
    from {
        transform: translateY(0);
        opacity: 1;
    }
    to {
        transform: translateY(-100px);
        opacity: 0;
    }
}
`;
document.head.appendChild(styleEl);

console.log('✅ Fetch Helper جاهز');
