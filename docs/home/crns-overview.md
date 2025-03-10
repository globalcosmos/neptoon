
## An overview of the technology
### How does it work?

A Cosmic-Ray Neutron Sensor (CRNS) is a passive sensor that detects neutrons passing through it. So whilst we think of it as a soil moisture sensor, what it actually senses is neutrons. Neutrons are omnipresent on Earth and get created by the natural cosmic background radiation. Deep in the soil, cosmic ray interactions lead to the production of so-called epithermal (or fast) neutrons. These fast neutrons get slowed down when they crash into with atoms in their path. Hydrogen, owing to it's size and weight, has the greatest influence on the number of neutrons which become thermalised (or to put it another way - the number of fast neutrons that are "slowed down"). As our CRNSs are primarily detecting neutrons in the epithermal/fast range, this leads to a strong inverse releationship between the count rate of the sensor, and the amount of soil moisture in the surrounding the sensor. 

![[CRNS_Overview.png]]

One of the key benefits of a CRNS is that it estimates the so-called "field scale" of soil moisture at root-zone depths, capturing soil moisture dynamics at a scale bridging the gap between more traditional point scale sensors, and coarser satellite remote sensing soil moisture products. 

![[CRNS_scales.png]]

### So more neutrons equals less soil moisture?

Not quite. There are other influences on the epithermal neutron count rate. One of the main goals in CRNS data processing is to remove this additional noise from the signal. After this we are left with only the changes in neutron count rates, representing  changes in soil moisture. Over the years our understanding of how to process CRNS has grown and changes (and continues to do so). This means that by now there are mutliple ways to apply some of these corrections. In neptoon we provide all the published methods for neutron corrections so that users can choose what processing steps to apply. We are also working with the CRNS community to present a best practice configuration file so users can get going quickly without becoming experts in CRNS (more on this in the [configuration](intro-to-config.md) section).

### Anything else?

Yes, like all data processing workflows there are multiple steps to achieve the best outcome. 

#### Sensor Calibration

To calibrate a sensor we need to find the N0 number. This is the theoretical number of neutrons that would be counted if there was no soil moisture at all (due to the inverse nature this is the **highest** count rate we would expect). This is often achieved by taking samples in the footprint of the sensor and using oven drying method (for maximum accuracy!). We then weight these samples according to the latest understanding (Schrön et al., 2017), and compare this to the count rate during the calibration campaign. This might seem a little complicated, but we provide easy to use methods in neptoon for this.

#### Quality Assessment

We also need to do some Quality Assessment on our data to ensure we are only correcting good data. For this we use [SaQC](https://rdm-software.pages.ufz.de/saqc/index.html) as our backend, integrating it directly into neptoon. This means we can focus on neutron correction methods and leave the quality assessment methods to the experts. 

#### Uncertainty estimation

Neutron count rates follow poisson statistics, with regards to their uncertainty. That means there is an inherent uncertainty which it's important to be aware of. In neptoon we calculate this and produce upper and lower bounds to soil moisture estimates.

#### Data Smoothing

To address noise in the signal its often a good idea to do some data smoothing.


