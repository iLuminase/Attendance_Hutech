// Clock Web Worker
self.onmessage = function (e) {
    if (e.data.start) {
        // Start the clock
        setInterval(() => {
            const now = new Date();
            const timeString = now.toLocaleString('vi-VN', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });

            // Send time back to main thread
            self.postMessage({
                time: timeString,
                timestamp: now.getTime(),
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
            });
        }, 1000);
    }
};