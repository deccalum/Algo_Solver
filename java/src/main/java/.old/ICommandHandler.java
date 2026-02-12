
/**
 * Interface for handling user commands during simulation
 */

public interface ICommandHandler {
    /**
     * Start listening for and processing user commands
     * This is a blocking call that runs until user quits
     */
    void handleCommands();
    
    /**
     * Stop command handling
     */
    void stop();
}
