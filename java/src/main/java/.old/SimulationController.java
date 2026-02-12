
import java.time.LocalDateTime;

/**
 * Controls simulation lifecycle events like month-end processing
 */
public class SimulationController implements ISimulationController {
    private final TimeSimulator timeSimulator;
    private final BusinessHours businessHours;
    private final OrderProcessor orderProcessor;
    private final MonthlyReport monthlyReport;
    private final Store store;
    
    private boolean monitoring = false;
    private Thread monitorThread;
    private int previousMonth = -1;
    private int previousDay = -1;
    
    public SimulationController(TimeSimulator timeSimulator, BusinessHours businessHours,
                               OrderProcessor orderProcessor, MonthlyReport monthlyReport, Store store) {
        this.timeSimulator = timeSimulator;
        this.businessHours = businessHours;
        this.orderProcessor = orderProcessor;
        this.monthlyReport = monthlyReport;
        this.store = store;
        // Seed with current simulated date to avoid immediate false rollovers
        var now = timeSimulator.getCurrentSimTime();
        this.previousMonth = now.getMonthValue();
        this.previousDay = now.getDayOfMonth();
    }
    
    @Override
    public void startMonitoring() {
        if (monitoring) {
            return;
        }
        
        monitoring = true;
        monitorThread = new Thread(this::checkMonthEnd);
        monitorThread.start();
    }
    
    @Override
    public void stopMonitoring() {
        monitoring = false;
        if (monitorThread != null) {
            monitorThread.interrupt();
        }
    }
    
    @Override
    public boolean isMonitoring() {
        return monitoring;
    }
    
    private void checkMonthEnd() {
        while (monitoring) {
            try {
                Thread.sleep(1000); // Check every second
                
                LocalDateTime now = timeSimulator.getCurrentSimTime();
                int currentDay = now.getDayOfMonth();
                int currentMonth = now.getMonthValue();

                // Detect day rollover
                if (currentDay != previousDay) {
                    previousDay = currentDay;
                    var totals = Log.calculateDayTotals(now.minusDays(1).toLocalDate());
                    Log.logDailySummary(totals.day().toString(), totals.orders(), totals.revenue());
                    System.out.println("DAILY SUMMARY: " + Log.readLatestDailySummary());
                }

                // Detect month rollover
                if (currentMonth != previousMonth) {
                    previousMonth = currentMonth;

                    // Month totals from log (ensures we report even if timing skips exact minute)
                    var monthTotals = Log.calculateMonthTotals(java.time.YearMonth.from(now.minusMonths(1)));

                    String report = monthlyReport.generateReport(now.minusMonths(1));
                    Log.logMonthlySummary(now.minusMonths(1).getMonth().toString() + " " + now.minusMonths(1).getYear(), report);
                    System.out.println("MONTHLY LOG ENTRY (from log): \n" + Log.readLatestMonthlySummary());

                    // If profit is negative, take a loan to cover the gap
                    double netProfit = monthlyReport.getTotalRevenue() - monthlyReport.getTotalCostOfGoodsSold() - store.getSpending();
                    if (netProfit < 0) {
                        store.takeLoan(-netProfit);
                    }

                    // Restock inventory at month boundary
                    store.restockLowStockMonthly();

                    // Reset counters for next month
                    monthlyReport.resetMonthlyCounters();

                    // Process any queued orders
                    businessHours.processQueuedOrders(orderProcessor);

                    // Print concise month totals from log for quick view
                    System.out.println("MONTH SUMMARY (from log): month=" + monthTotals.month() + ", orders=" + monthTotals.orders() + ", revenue=" + String.format("%.2f", monthTotals.revenue()));
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

}
