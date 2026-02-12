
public class Main {
    private final TimeSimulator timeSimulator;
    private final Store store;
    private final OrderProcessor orderProcessor;
    private final BusinessHours businessHours;
    private final MonthlyReport monthlyReport;
    
    private final IOrderGenerator orderGenerator;
    private final ISimulationController simulationController;
    private final ICommandHandler commandHandler;

    public Main() {
        this.store = new Store();
        this.businessHours = new BusinessHours();
        this.timeSimulator = new TimeSimulator();
        this.orderProcessor = new OrderProcessor(businessHours);
        this.monthlyReport = new MonthlyReport(store);
        
        // Initialize new components using interfaces
        this.orderGenerator = new OrderGenerator(store, timeSimulator, orderProcessor, monthlyReport);
        this.simulationController = new SimulationController(timeSimulator, businessHours, orderProcessor, monthlyReport, store);
        this.commandHandler = new CommandHandler(timeSimulator, businessHours, monthlyReport);
    }

    public static void main(String[] args) {
        Main simulator = new Main();
        simulator.start();
    }

    public void start() {
        System.out.println("Starting Shop Simulator: " + store.getName());
        System.out.println("Store Size: " + store.getSize());
        System.out.println("Initial Budget: $" + store.budget());

        // Initial speed 720x
        System.out.println("Setting simulation to Turbo Speed (720x) - 1 Month ≈ 1 Minute");
        timeSimulator.setSpeed(720);

        // Start time simulation
        Thread timeThread = new Thread(() -> timeSimulator.tick());
        timeThread.start();

        // Start order generation
        orderGenerator.startGenerating();

        // Start month-end monitoring
        simulationController.startMonitoring();

        // Start handling user commands (blocks the main thread)
        commandHandler.handleCommands();

        // Cleanup
        timeSimulator.stop();
        orderGenerator.stopGenerating();
        simulationController.stopMonitoring();
        orderProcessor.shutdown();
    }
}

