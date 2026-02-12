
/**
 * Interface for controlling simulation lifecycle events
 */

public interface ISimulationController {
    /**
     * Start monitoring simulation events (month-end, etc.)
     */
    void startMonitoring();
    
    /**
     * Stop monitoring simulation events
     */
    void stopMonitoring();
    
    /**
     * Check if controller is currently monitoring
     * @return true if monitoring, false otherwise
     */
    boolean isMonitoring();
}
