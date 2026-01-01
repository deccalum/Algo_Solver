package se.lexicon;

import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicBoolean;

public class TimeSimulator {
    private int speedMultiplier = 4; // Default: 4x speed
    private LocalDateTime simTime;
    private final AtomicBoolean isRunning = new AtomicBoolean(true);
    private LocalDateTime lastMonthEndCheck;

    public TimeSimulator() {
        this.simTime = LocalDateTime.now();
        this.lastMonthEndCheck = simTime;
    }

    public void setSpeed(int multiplier) {
        if (multiplier == 1 || multiplier == 4 || multiplier == 8 || multiplier == 32) {
            this.speedMultiplier = multiplier;
            System.out.println("Speed set to " + multiplier + "x");
        } else {
            System.out.println("Invalid speed. Use 1, 4, 8, or 32.");
        }
    }

    public void tick() {
        try {
            while (isRunning.get()) {
                long sleepTime = 1000 / speedMultiplier;
                Thread.sleep(sleepTime);
                simTime = simTime.plusMinutes(1);
                
                // Check for month end
                if (isMonthEnd()) {
                    System.out.println("MONTH END REACHED: " + simTime);
                    lastMonthEndCheck = simTime;
                }
            }
        } catch (InterruptedException ex) {
            System.getLogger(TimeSimulator.class.getName())
                    .log(System.Logger.Level.ERROR, "TimeSimulator interrupted", ex);
            Thread.currentThread().interrupt();
        }
    }

    public synchronized LocalDateTime getCurrentSimTime() {
        return simTime;
    }

    public boolean isMonthEnd() {
        int dayOfMonth = simTime.getDayOfMonth();
        int lastDayOfMonth = simTime.toLocalDate().lengthOfMonth();
        return dayOfMonth == lastDayOfMonth && simTime.getHour() == 23 && simTime.getMinute() == 59;
    }

    public void stop() {
        isRunning.set(false);
    }

    public boolean isRunning() {
        return isRunning.get();
    }

    public int getSpeedMultiplier() {
        return speedMultiplier;
    }
}