// 🔥 CÁCH 2: Vanilla JavaScript với requestAnimationFrame
export class VanillaClockService {
    private animationId: number = 0;
    private callback: (time: string) => void = () => { };

    startClock(updateCallback: (time: string) => void) {
        this.callback = updateCallback;
        this.tick();
    }

    private tick = () => {
        const now = new Date();
        const timeString = this.formatTime(now);
        this.callback(timeString);
        this.animationId = requestAnimationFrame(this.tick);
    }

    private formatTime(date: Date): string {
        return date.toLocaleString('vi-VN', {
            weekday: 'short',
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    stopClock() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// 🔥 CÁCH 3: Performance-based Clock
export class PerformanceClockService {
    private startTime = performance.now();
    private intervalId: any;

    startPerformanceClock(callback: (time: string) => void) {
        this.intervalId = setInterval(() => {
            const elapsed = performance.now() - this.startTime;
            const now = new Date();
            const perfTime = `${now.toLocaleTimeString('vi-VN')} (+${Math.floor(elapsed / 1000)}s)`;
            callback(perfTime);
        }, 100); // Update every 100ms for smoother animation
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }
}

// 🔥 CÁCH 4: Multiple Timezone Clock
export class WorldClockService {
    getWorldTimes(): { [key: string]: string } {
        const now = new Date();
        return {
            vietnam: now.toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' }),
            usa: now.toLocaleString('en-US', { timeZone: 'America/New_York' }),
            japan: now.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }),
            london: now.toLocaleString('en-GB', { timeZone: 'Europe/London' })
        };
    }

    startWorldClock(callback: (times: { [key: string]: string }) => void) {
        return setInterval(() => {
            callback(this.getWorldTimes());
        }, 1000);
    }
}

// 🔥 CÁCH 5: Animated Digital Clock với LED effect
export class LEDClockService {
    generateLEDTime(): { time: string; segments: string[] } {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });

        // Convert to LED segments (simplified)
        const segments = timeStr.split('').map(char => {
            switch (char) {
                case '0': return '█████\n█   █\n█   █\n█   █\n█████';
                case '1': return '    █\n    █\n    █\n    █\n    █';
                case '2': return '█████\n    █\n█████\n█    \n█████';
                case '3': return '█████\n    █\n█████\n    █\n█████';
                case '4': return '█   █\n█   █\n█████\n    █\n    █';
                case '5': return '█████\n█    \n█████\n    █\n█████';
                case '6': return '█████\n█    \n█████\n█   █\n█████';
                case '7': return '█████\n    █\n    █\n    █\n    █';
                case '8': return '█████\n█   █\n█████\n█   █\n█████';
                case '9': return '█████\n█   █\n█████\n    █\n█████';
                case ':': return '  \n██\n  \n██\n  ';
                default: return '     \n     \n     \n     \n     ';
            }
        });

        return { time: timeStr, segments };
    }
}