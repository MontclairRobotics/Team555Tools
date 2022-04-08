package org.team555.frc.leds;

import edu.wpi.first.wpilibj.AddressableLEDBuffer;
import edu.wpi.first.wpilibj.util.Color;
import edu.wpi.first.wpilibj.util.Color8Bit;

public interface LedColor 
{
    public static Color rgb(double r, double g, double b)
    {
        return new Color(r, g, b);
    }
    public static Color rgb8(int r, int g, int b)
    {
        return new Color(new Color8Bit(r, g, b));
    }
    public static Color hsv(double h, double s, double v)
    {
        return Color.fromHSV((int)(h * 255), (int)(s * 255), (int)(v * 255));
    }
    public static Color hsv8(int h, int s, int v)
    {
        return Color.fromHSV(h, s, v);
    }
}
