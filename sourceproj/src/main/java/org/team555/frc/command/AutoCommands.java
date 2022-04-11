package org.team555.frc.command;

import java.security.InvalidAlgorithmParameterException;
import java.util.HashMap;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.Supplier;

import edu.wpi.first.util.sendable.Sendable;
import edu.wpi.first.wpilibj.smartdashboard.SendableChooser;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.Command;

/**
 * Class which holds all the autonomous commands and
 * sets the default autoCommand
 * 
 * @author Team 555 (Dylan Rafael)
 * @version 1.0
 * @since 1.0
 */
public final class AutoCommands 
{
    private AutoCommands() {}

    /** 
     * the commands are held in a HashMap
     * The keys are the  names of the auto commands as a Strings
     * The values are the commands themselves 
     */
    private static final Map<String, Supplier<Command>> commands = new HashMap<>();

    // Settings
    private static String defaultAutoCommand = "Main";

    public static void setDefaultAutoCommand(String value)
    {defaultAutoCommand = value;}
    
    public static void add(String name, Supplier<Command> command)
    {
        commands.put(name, command);
    }
    public static Command get(String name)
    {
        return commands.get(name).get();
    }

    private static SendableChooser<Command> chooserInternal;
    public static SendableChooser<Command> chooser()
    {
        if(chooserInternal != null)
        {
            return chooserInternal;
        }

        var s = new SendableChooser<Command>();

        if(!commands.containsKey(defaultAutoCommand))
        {
            throw new IllegalArgumentException("Default state (" + defaultAutoCommand + ") does not exist!");
        }

        s.setDefaultOption(defaultAutoCommand, get(defaultAutoCommand));

        for(var name : commands.keySet())
        {
            if(name.equals(defaultAutoCommand))
            {
                continue;
            }

            s.addOption(name, get(name));
        }

        chooserInternal = s;

        return s;
    }
}
