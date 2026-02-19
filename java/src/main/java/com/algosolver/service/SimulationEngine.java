package com.algosolver.service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.algosolver.service.enums.Speed;
import lombok.Setter;

public class SimulationEngine {

    private static final Logger LOGGER = Logger.getLogger(SimulationEngine.class.getName());

    @Setter
    private Speed speed = Speed.X1;
    private final AtomicBoolean running = new AtomicBoolean(false);
    private final SimulationState state;
    private LocalDateTime simTime;
    private LocalDate lastProcessedDate;

    public SimulationEngine(SimulationState state) {
        this.state = state;
        this.simTime = state.getStartDate().atStartOfDay();
        this.lastProcessedDate = state.getStartDate();
    }

    public void start() {
        if (running.compareAndSet(false, true)) {
            new Thread(this::tick, "SimulationEngine").start();
        }
    }

    private void tick() {
        try {
            while (running.get()) {
                long sleepTime = 1000 / speed.getValue();
                Thread.sleep(sleepTime);

                simTime = simTime.plusMinutes(1);
                LocalDate currentDate = simTime.toLocalDate();

                if (!currentDate.equals(lastProcessedDate)) {
                    lastProcessedDate = currentDate;
                }
            }
        } catch (InterruptedException ex) {
            LOGGER.log(Level.WARNING, "SimulationEngine interrupted", ex);
            Thread.currentThread().interrupt();
        }
    }

    public synchronized LocalDate getCurrentSimDate() {
        return simTime.toLocalDate();
    }

    public synchronized LocalDateTime getCurrentSimTime() {
        return simTime;
    }

    public void pause() {
        running.set(false);
    }

    public void stop() {
        running.set(false);
    }

    public boolean isRunning() {
        return running.get();
    }

    public Speed getSpeed() {
        return speed;
    }

    public SimulationState getState() {
        return state;
    }
}