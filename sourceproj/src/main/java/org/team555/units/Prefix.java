package org.team555.units;

/**
 * Class which holds all the information regarding prefixes
 * for Units consiting of name, prefix, and the modifier
 * 
 * @author Team 555 (Dylan Rafael)
 * @version 1.0
 * @since 1.0
 */
public class Prefix 
{
    private final String name;
    private final String prefix;
    private final double modifier;

    public String name() { return name; }
    public String prefix() { return prefix; }
    public double modifier() { return modifier; }

    public Prefix(String name, String prefix, double modifier)
    {
        this.name = name;
        this.prefix = prefix;
        this.modifier = modifier;
    }

    /**
     * Create a Unit of measurement based on another unit and 
     * the prefix created
     * 
     * @param unit
     */
    public Unit of(Unit unit)
    {
        var u = Unit.from(
            name + unit.name(),
            name + unit.pluralName(), 
            prefix + unit.symbol(),
            unit.value / modifier, 
            unit.dim
        );
        return u;
    }

    /**
     * Creates a prefix from the givin information
     * 
     * @param name : the prefix itself
     * @param prefix : the abbreviation of the prefix
     * @param modifier : the number to multiply the base value by to equal the value of prefix+unit
     */
    public static Prefix from(String name, String prefix, double modifier)
    {
        return new Prefix(name, prefix, modifier);
    }
}
