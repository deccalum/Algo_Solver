
/**
 * Interface for generating customer orders in the simulation.
 */

public interface IOrderGenerator {
    /**
     * Start generating orders based on store size and configuration
     */
    void startGenerating();
    
    /**
     * Stop generating new orders
     */
    void stopGenerating();
    
    /**
     * Check if order generation is currently running
     * @return true if generating orders, false otherwise
     */
    boolean isGenerating();
}
