# Smittestop Epaper


## Customization

Your fleet of Inkyshots can all be managed centrally via balenaCloud. Try any of the environment variables below to add some customization.

### Timezone

In order for the update time to work correctly, you'll of course have to tell Inkyshot what timezone you'd like to use. Set the `TZ` environment variable to any [IANA timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), e.g. `Europe/London`, `America/Los_Angeles`, `Asia/Taipei` etc.

#
## Case

STL files are included within the assets folder of the project for you to 3D print your own case.

![](https://raw.githubusercontent.com/balenalabs-incubator/inkyshot/master/assets/inky-print.png)

The case has two positions for a captive M3 nut, and can be fastened together with two countersunk 8mm M3 machine screws.

A position is open in the rear of the case for the use of a [micro USB PCB socket](https://www.aliexpress.com/item/4000484202812.html), allowing for direct connection of power to the back of a Raspberry Pi Zero.

![](https://raw.githubusercontent.com/balenalabs-incubator/inkyshot/master/assets/inky-rear.png)



