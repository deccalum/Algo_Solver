package service;

import java.time.LocalDate;

import model.Region;
import model.World;

public class SimulationState {

    private final LocalDate startDate;
    private final World world;
    private final Region region;

    public SimulationState(LocalDate startDate, World world, Region region) {
        this.startDate = startDate;
        this.world = world;
        this.region = region;
    }

    public LocalDate getStartDate() {
        return startDate;
    }
    
    public World getWorld() {
        return world;
    }

    public Region getRegion() {
        return region;
    }
}
