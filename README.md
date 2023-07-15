# aiopypiserver
Just an idea ATM - reimplement pypiserver with aiohttp as the web server

The motivation for this was a desire to run pypiserver behind an apache proxy
serving multiple different applications and the need to support relative paths.
I am also keen for this to use a more current solution, ie aiohttp.
