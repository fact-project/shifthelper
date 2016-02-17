This document aims to serve as a rationale for the creation of the program `shifthelper`. 
It should also clarify certain design decisions.


# Status of operation before

We write the year 2015 and the typical FACT night shift goes smooth. Shifters still need to restart `Main.js` quite often. 
And the startup in the evening and the shutdown in the morning are a tiny bit more effort than today (2016). 
During the night, the shifter can basically study or watch movies, while keeping an eye on the DAQ and the weather. 

We were training some new colleagues for the night shift and had to answer a lot of questions like:
 
* When the `Main.js` program throws an exception, and I find nothing that looks hooribly wrong. Can I just try to restart it once?
* In the instructions it says: "At high winds for longer time, park the telescope" What exactly do you mean by high winds and longer time?
* Here it says: "If the currents are high for a longer time, and there is no other source available, park the telescope", What exactly do you mean by high currents? What exactly do you mean by longer time?

The instructions were quite clear but not giving precise numbers in all cases. 
Leaving the decision to people who had no prior experience with the FACT hardware would either mean, 
letting them choose the save way and loose a lot of data,
or letting the choose the wrong way and maybe loose the camera. 
So we had no choice but taking the decision for them in advance. 
We needed to provide more detailed specifications based on our prior knowledge.

This reminded me of a book about software design I read once.

```
 [...] specifying requirements in such detail [...] is programming. Such a specification is code.
```

This was the time, when we first thought: This can all be scripted.


# Missing no alarm

The browser based smartfact program was already in place and helping a lot. One still needed the shell on La Palma 
back then for startup and shutdown, but only then. During the night your ssh-connection could break and you wouldn't 
notice until the morning, when you tried to close the lid.

smartfact was also very helpful in not forgetting about the different security limits. Assume currents were rising but you 
happened to forget about the limit. smartfact helped you by sounding an alarm when the currents rose to high. The same for 
high wind and rain. Also when for some reason the DAQ boards had a problem and blocked. 
Then you got an alarm telling you the trigger rate just went to zero.

However by far the most common reason for manual interaction at that time was for the top level program, 
which controlled everything, to throw an exception and stop. This did not cause an alarm but just a faint 'bing'.

So it happened that people were walking around their house missing that 'bing' 
and something around 30minutes of data were lost, before they realized.


# Flare Alerts

At some point we decided to send around flare alerts from FACT to interested people in the Cherenkov community. 
Night shifters now needed to decide if a source was flaring or not based on the QLA results, and in case it flared call 
Daniela Dorner in order to compile the according message. Depending on the binning every 5 to 20 minutes a new point would be added
to the QLA plot and while studying or working, I typically used an alarm clock to remind me another 20minutes had passed, so I wouldn't 
forget to check the QLA plot.

While specific flare alert limits were missing at first, after a while 
clear specifications were given in terms of excess events and significance, about when a flare limit is reached. 

You can guess it already. This needed to be scripted. Why would I look at a plot every 20 minutes to see no flare,
if the plot can also alert me, if it contains a flare? 


# Summary


