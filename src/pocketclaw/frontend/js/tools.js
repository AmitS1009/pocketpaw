/**
 * PocketClaw Tools Module
 * Handles tool-specific UI interactions and formatting
 */

const Tools = {
    /**
     * Format message content (markdown-like)
     */
    formatMessage(content) {
        if (!content) return '';
        
        // Escape HTML first
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Code blocks
        formatted = formatted.replace(
            /```(\w*)\n?([\s\S]*?)```/g,
            '<pre><code>$2</code></pre>'
        );
        
        // Inline code
        formatted = formatted.replace(
            /`([^`]+)`/g,
            '<code>$1</code>'
        );
        
        // Bold
        formatted = formatted.replace(
            /\*\*(.+?)\*\*/g,
            '<strong>$1</strong>'
        );
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    },

    /**
     * Format current time
     */
    formatTime(date = new Date()) {
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', container) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-msg">${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 3s
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    /**
     * Parse system status from response
     */
    parseStatus(content) {
        const status = {
            cpu: '—',
            ram: '—',
            disk: '—',
            battery: '—'
        };
        
        if (!content) return status;
        
        // Parse CPU: "🧠 CPU: 50.0% (8 cores)"
        const cpuMatch = content.match(/CPU:\s*([\d.]+)%/);
        if (cpuMatch) status.cpu = Math.round(parseFloat(cpuMatch[1]));
        
        // Parse RAM: "💾 RAM: 10.0 / 16.0 GB (60%)"
        const ramMatch = content.match(/RAM:.*?\(([\d.]+)%\)/);
        if (ramMatch) status.ram = Math.round(parseFloat(ramMatch[1]));
        
        // Parse Disk: "💿 Disk: 200 / 500 GB (40%)"
        const diskMatch = content.match(/Disk:.*?\(([\d.]+)%\)/);
        if (diskMatch) status.disk = Math.round(parseFloat(diskMatch[1]));
        
        // Parse Battery: "🔋 Battery: 80%"
        const batteryMatch = content.match(/Battery:\s*([\d.]+)%/);
        if (batteryMatch) status.battery = Math.round(parseFloat(batteryMatch[1]));
        
        return status;
    },

    /**
     * Check if content is a file browser response
     */
    isFileBrowser(content) {
        return content && content.includes('📁') && content.includes('📂');
    },

    /**
     * Check if content is a screenshot
     */
    isScreenshot(data) {
        return data.type === 'screenshot' && data.image;
    }
};

// Export
window.Tools = Tools;
