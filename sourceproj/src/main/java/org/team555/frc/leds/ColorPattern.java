package org.team555.frc.leds;

import java.util.function.Function;

import edu.wpi.first.wpilibj.AddressableLEDBuffer;

public class ColorPattern implements LedPattern
{
    private final ColorGetter getter;
    public ColorPattern(ColorGetter getter)
    {
        this.getter = getter;
    }

    @Override
    public void processInto(AddressableLEDBuffer led, int index, double deltaTime) 
    {
        led.setLED(index, getter.get());
    }
}
