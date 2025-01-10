'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 5
' Initial_Processdelay           = 1000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.0
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DUTTLAB8  Duttlab8\Duttlab
'<Header End>
'This script uses the automatic check every 10ns on the digital inputs and
'triggers an increment of Par_1 if it detects a falling edge on ANY channel 

#Include ADwinGoldII.inc



init:
  Par_1 = 0
  Par_2 = 0
  Conf_DIO(1100b) 'Configures digital pins 0-15 as inputs and 16-31 as outputs
  
event:
  Par_1 = Digin_Edge(1)   'Bit string where each bit corresponds to if the channel saw a rising edge
  IF (Par_1 > 0) THEN     'If a channel saw a rising edge bit string = [LONG] with be > 1
    Inc(Par_2)            'Example of what happens when a rising edge is detected
  ENDIF


