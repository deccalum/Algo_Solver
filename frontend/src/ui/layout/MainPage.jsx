import InitializationControls from "../steps/Initialization";
import GenerationControls from "../steps/GenerationControls";
import styles from "../styles/MainPage.module.css";

export default function MainPage() {
    return (
        <div className={styles.wrapper}>
            <section className={styles.section}>
                <InitializationControls />
            </section>

            <section
                id="generation-section"
                className={styles.section}
            >
                <GenerationControls />
            </section>
        </div>
    );
}
