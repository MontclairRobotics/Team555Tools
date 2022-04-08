package org.team555.frc.leds;

import edu.wpi.first.wpilibj.AddressableLEDBuffer;
import edu.wpi.first.wpilibj.util.Color;

public interface LedPattern 
{
    void processInto(AddressableLEDBuffer led, int index, double deltaTime);

    public static LedPattern ofColor(Color color)
    {
        return new ColorPattern(() -> color);
    }
    public static LedPattern ofColor(ColorGetter getter)
    {
        return new ColorPattern(getter);
    }
}
