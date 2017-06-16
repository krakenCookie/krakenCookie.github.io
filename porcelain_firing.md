
# My Shapeways problem

# What I want to do

I want to 3D print a custom keyboard case for a certain type of half-keyboard in porcelain.  

Because this porcelain is going to be 
holding a relatively precise steel plate, I'd like the surfaces holding it to be as flat and as even as possible.  I don't think this will be a problem if the case is laying horizontally like it would on a table--gravity should distribute the glaze relatively evenly over the flat horizontal surfaces that will hold the plate.

# My model specifications

The dimensions of my model are roughly **150 x 110 x 30 mm** (*x*, *y*, *z*). 

Below you can see the model in the orientation I would like it to be fired in:

<img src="http://burchill.github.io/images/desired_orientation.png" width="500" />

# The problem: the 3D printer's bounding box

However, the maximum bounding box of the printer is **125 x 125 x 200 mm**.  The best possible solution for me would be that the printer does not strictly need to print in this orientation.  If the direction of the printer could be changed, or it could be rotated or something to that extent, then the rest of the possible solutions I discuss are pointless--we could just make it so that it prints the model in something like the orientation in the image above.

But if it can't, and the *z*-axis *has* to be parellel with the pull of gravity, my model can still fit in this bounding box if rotated--for example if I rotate it 90 degrees around the x-axis, so that it becomes **30 x 110 x 150 mm**.

# Possible solutions:

If the printer can't be rotated (or something like that) and we need to print my model at a different orientation, I came up with a few possible ways that could be accomplished. I don't know your system, so I just threw out a few possible ideas and my concerns about what they might necessitate.

Most of the following potential solutions are built on the idea that we can *print* the model in the bounding box with an orientation so that it fits (e.g., rotated 90 degrees), and then fire the ceramic in the desired orientation pictured above.  If there's some sort of reason why that couldn't be done, I think I'm basically out of luck, but hopefully not.

## Rotating the model 90 degrees

The most straightforward potential solution would be to do precisely what I just described--rotate it 90 degrees.

The image below shows how that would look:

<img src="http://burchill.github.io/images/in_the_bbox.png" width="500" />

### Potential problem: the curved side deforming

I don't know how the 3D printer is set up, or *how* it can be set up, but depending on the orientation, printing process, and the firmness of the material, I'm not sure if the side of the model that's now touching the x-y plane would retain its shape.

You can see here that the area touching that plane isn't flat:

<img src="http://burchill.github.io/images/detail_of_ground_contact.png" width="500" />

It seems likely that this side of the model might get squished or deformed by the weight of the rest of the model, which I'd like to avoid.

## Rotating the model 90 degrees *and* changing its shape

If the above solution *would* deform the shape of the side of the model touching the x-y plane, I could change it, although I would very much prefer not to.  I could make it flat and have it be something like this:

<img src="http://burchill.github.io/images/less_desirable_solution.png" width="500" />

### Potential problem: other sides deforming

Even if this less desirable solution would prevent the bottom side from deforming, I'm worried that the other sides of the model might bow due to gravity.  If the model were printed horizontally, the support of the ground would help prevent the walls from bowing, but if it were vertical as in these solutions, they might bend.

## Rotating less and using supports

Another option that I could come up with, but would also be less desirable would be to rotate the model less than 90 degrees, and support it with support structures.  For example, if rotate ~30 degrees or so, the model can still fit in the bounding box, but it would be at an angle that it couldn't stand upright by itself.  To make sure it doesn't fall over, I could add some support structures like the ones shown below.  

<img src="http://burchill.github.io/images/support.png" width="500" />

I'd probably have to make the supports better than what you can see above, as well as including some for the bottom--this is just a mock-up.

### Potential problem: glazing angle and removing supports

The biggest problem with this approach is that I would really prefer for it not to be fired and glazed at this angle--my final model is probably going to have some holes/depressions in it, and don't want to the glaze to pool asymmetrically due to the tilting angle.  

Secondly, I'd really prefer not to have to file off the support structures by hand after it's been fired and glazed and sent to me.

I know that there is some manual touch-up done to the model before and after firing--is it possible that someone could remove the support structures after it's printed, but before it's fired?  That way, we could print it at this more gentle angle, but fire it in the proper orientation.  If this is possible, I would prefer to the solution where I have to change the side of the model.

# Feedback

Thank you so much for your great customer support--hopefully this helps us get a solution that ends up working. 

Due to my somewhat limited knowledge of 3D printing, I might have also missed some solutions that could be even better. The potential solutions I mention here were just the only options I could think of.





