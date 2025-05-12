
![[Pasted image 20240917171150.png]]

neptoon is a python tool for processing Cosmic-Ray Neutron Sensors (CRNS). CRNS estimate soil moisture at the field scale, and up to root-zone depths, by tracking changes in the number of fast neutrons found at a particular location. This is primarily due to the strong inverse relationship between the number of hydrogen atoms and the number of fast neutrons. To have estimates of only the impact of hydrogen in soil moisture, additional processing and correction steps are required. Our understanding of the sensor continues to grow and change, which brings about an increasing number of theories and equations that can be applied. 

Neptoon is designed to facilitate the painless processing of CRNS sites, utilising the most current techniques and knowledge available. It is designed to be simple to use for those who wish to simply correct a sensor with the most current understanding, as well as full featured for researchers in the CRNS space who want to experiment and test new ideas. 

!!! warning "Work in Progress"
	The documentation is still under construction and so a brief warning that some of the suggested actions may be unclear or incomplete. Check back soon!

## Install

<div class="grid">
<a href="user-guide/installation" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Install</h3> <p>Learn how to install neptoon on your system</p> </div> </a>
</div>

## Introduction

<div class="grid">

<a href="home/crns-overview" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>How does Cosmic-Ray Neutron Sensing work?</h3> <p>An overview on how the CRNS technology works, and the steps required to go from neutrons to soil moisture</p> </div> </a>

<a href="home/key-features" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Key neptoon features</h3> <p>An explanation of what neptoon can do (with links to more details)</p> </div> </a>


</div>

## User Guides

<div class="grid">
<a href="user-guide/workflow-description" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Workflow overview</h3> <p>Understand a little more about the workflow - from neutrons to soil mositure</p> </div> </a>
<!-- <a href="user-guide/installation" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Core concepts</h3> <p>Here we go over some of the concepts and architecture in neptoon. Warning: we get a little more technical here.</p> </div> </a> -->
<a href="user-guide/the-neptoon-GUI" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Graphical User Interface</h3> <p>Neptoon has been designed with a simple to user GUI, learn about that here.</p> </div> </a>
<a href="user-guide/process-with-config/intro-to-config" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Configuration Files</h3> <p>How to prepare and use configuration files for fast (and reproduceable!) processing.</p> </div> </a>


<a href="user-guide/python-ide-overview" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Using neptoon in your PythonIDE</h3> <p>Learn how to use the GUI to process a site with simply your data, and some config files</p> </div> </a>

<a href="user-guide/sensor-calibration" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Calibration</h3> <p>Need to calibrate your site? Check this out.</p> </div> </a>
<a href="user-guide/neptoon-examples" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Examples!</h3> <p>Here we present examples we have made to help you understand Neptoon and start working with it.</p> </div> </a>
</div>

## Advanced User Guide
TBC

## More information

<div class="grid">
<a href="home/roadmap" class="card"> <div class="card-content"> <i class="fas fa-download"></i> <h3>Roadmap</h3> <p>Sneak a peak at some future plans with neptoon</p> </div> </a>
</div>

## Support

daniel.power@ufz.de

martin.schroen@ufz.de

## Contributing 

!!! warning "Work in Progress"
	This section is not yet complete. 

If you want to contribute to neptoon we are always open to ideas. The goal is for this to be a useful tool for everyone to adapt and change to their CRNS needs!


## Authors and acknowledgment

Lead Developers:

- Daniel Power (daniel.power@ufz.de)
- Martin Schrön (martin.schroen@ufz.de)

We would also like to acknowledge the following people and groups for continued support during the development of neptoon.

- Fredo Erxleben	
- Steffen Zacharias
- Rafael Rosolem
- Miguel Rico-Ramirez

<!-- 
![alt text](assets/ufz.png) ![alt text](assets/bristol.png) 

![alt text](assets/elter.png) ![alt text](assets/envrinnov.png) ![alt text]()
 -->

## License

MIT License

