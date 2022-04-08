package org.team555.frc.leds;

import edu.wpi.first.wpilibj.AddressableLEDBuffer;
import edu.wpi.first.wpilibj.util.Color;

@FunctionalInterface
public interface ColorGetter
{
    public Color get();
}
