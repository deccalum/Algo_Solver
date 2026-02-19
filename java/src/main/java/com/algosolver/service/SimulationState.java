package com.algosolver.service;

import java.time.LocalDate;

import com.algosolver.model.Region;
import com.algosolver.model.World;
import lombok.Getter;

@Getter

public class SimulationState {

    private final LocalDate startDate;
    private final World world;
    private final Region region;

    public SimulationState(LocalDate startDate, World world, Region region) {
        this.startDate = startDate;
        this.world = world;
        this.region = region;
    }

}