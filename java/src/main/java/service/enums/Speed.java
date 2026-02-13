package service.enums;

public enum Speed {

    X1(1), 
    X2(2), 
    X4(4), 
    X8(8), 
    X16(16), 
    X32(32), 
    X64(64), 
    X128(128), 
    X720(720);

    private final int multiplier;

    Speed(int multiplier) {
        this.multiplier = multiplier;
    }

    public int getValue() {
        return multiplier;
    }
}
