/**
 * Mobile-specific error handling utilities
 */

export class MobileErrorHandler {
  private static errorQueue: Array<{ message: string; details?: any }> = [];
  private static isShowing = false;

  /**
   * Handle mobile-specific errors with user-friendly messages
   */
  static async handleError(error: Error | string, details?: any) {
    // Add to queue
    this.errorQueue.push({
      message: typeof error === 'string' ? error : error.message,
      details
    });

    // Show error if not already showing one
    if (!this.isShowing) {
      this.showNextError();
    }

    // Log to console for debugging
    console.error('Mobile Error:', error, details);
  }

  private static async showNextError() {
    if (this.errorQueue.length === 0) {
      this.isShowing = false;
      return;
    }

    this.isShowing = true;
    const error = this.errorQueue.shift()!;

    try {
      // Use native alert on mobile as fallback
      if (this.isMobileDevice()) {
        // Try to use a toast notification first
        if (this.showToast) {
          this.showToast(error.message);
        } else {
          alert(error.message);
        }
      } else {
        // Desktop error handling
        console.error('Error:', error.message);
      }
    } catch (e) {
      // Fallback to console
      console.error('Error in error handler:', e);
    }

    // Wait before showing next error
    setTimeout(() => {
      this.showNextError();
    }, 3000);
  }

  /**
   * Check if device is mobile
   */
  private static isMobileDevice(): boolean {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  /**
   * Show toast notification (to be implemented by the app)
   */
  private static showToast?: (message: string) => void;

  /**
   * Set toast notification handler
   */
  static setToastHandler(handler: (message: string) => void) {
    this.showToast = handler;
  }

  /**
   * Handle network errors specifically
   */
  static handleNetworkError(error: any) {
    let message = '网络连接错误';
    
    if (error.name === 'NetworkError') {
      message = '网络连接失败，请检查网络设置';
    } else if (error.message.includes('fetch')) {
      message = '数据加载失败，请重试';
    } else if (navigator.onLine === false) {
      message = '设备已离线，请连接网络';
    }

    this.handleError(message, {
      type: 'network',
      online: navigator.onLine,
      error: error.message
    });
  }

  /**
   * Handle storage errors
   */
  static handleStorageError(error: any) {
    let message = '存储空间不足';
    
    if (error.name === 'QuotaExceededError') {
      message = '存储空间已满，请清理缓存';
    } else if (error.message.includes('storage')) {
      message = '数据保存失败，请重试';
    }

    this.handleError(message, {
      type: 'storage',
      error: error.message
    });
  }

  /**
   * Handle permission errors
   */
  static handlePermissionError(permission: string) {
    const messages: Record<string, string> = {
      'camera': '相机权限被拒绝，无法拍照',
      'microphone': '麦克风权限被拒绝，无法录音',
      'location': '位置权限被拒绝，无法获取位置',
      'notifications': '通知权限被拒绝，无法接收推送'
    };

    this.handleError(messages[permission] || `${permission}权限被拒绝`, {
      type: 'permission',
      permission
    });
  }
}

/**
 * Mobile-specific performance monitoring
 */
export class MobilePerformanceMonitor {
  private static metrics: Array<{ name: string; duration: number; timestamp: number }> = [];

  /**
   * Start measuring performance
   */
  static startMeasure(name: string): () => void {
    const start = performance.now();
    
    return () => {
      const duration = performance.now() - start;
      this.metrics.push({
        name,
        duration,
        timestamp: Date.now()
      });

      // Log slow operations
      if (duration > 100) {
        console.warn(`Slow operation: ${name} took ${duration.toFixed(2)}ms`);
      }

      // Keep only last 100 metrics
      if (this.metrics.length > 100) {
        this.metrics = this.metrics.slice(-100);
      }
    };
  }

  /**
   * Get performance metrics
   */
  static getMetrics() {
    return this.metrics;
  }

  /**
   * Clear metrics
   */
  static clearMetrics() {
    this.metrics = [];
  }

  /**
   * Check if device is low-end
   */
  static isLowEndDevice(): boolean {
    // Simple heuristics for low-end device detection
    const memoryLimit = 4 * 1024 * 1024 * 1024; // 4GB
    const coresLimit = 4;
    
    if ('deviceMemory' in navigator) {
      return (navigator as any).deviceMemory < 4;
    }
    
    if ('hardwareConcurrency' in navigator) {
      return navigator.hardwareConcurrency < 4;
    }
    
    return false;
  }

  /**
   * Optimize performance for low-end devices
   */
  static optimizeForLowEndDevice() {
    if (this.isLowEndDevice()) {
      // Reduce animations
      document.body.classList.add('reduce-motion');
      
      // Lazy load more aggressively
      // This would be implemented in the components
      
      console.log('Optimizing for low-end device');
    }
  }
}

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  MobilePerformanceMonitor.optimizeForLowEndDevice();
}