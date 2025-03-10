# file containing class definition and associated functions for the ball objects
from random import choice, uniform
from math import sqrt, hypot
import pygame as pg
from .constants import ballRadius, defaultColor, hoverColor, clickColor, boundaries, winWidth, winHeight, fixationCrossLength, velocityFactor
from .gameOptions import exactPhysicsEnabled

# == Defines the Objects (Balls) and their Properties ==
class Ball:

    # initializes a Ball instance
    def __init__(self, game):

        # size of the balls
        self.radius = ballRadius

        # Location of the balls on the screen (ensure they are within the screen and not on the borders)
        self.x = 0
        self.y = 0

        # Directional velocity of the balls
        self.dx, self.dy = self.velocity(game)

        # Start by setting the balls to the default color (currently white)
        self.color = defaultColor

        # -- State attributes for mouse selection control
        self.state = "neutral"
        self.isSelected = False
    
    def changeColor(self, color):
        self.color = color

    def inCircle(self, mouse_x, mouse_y):
        # -- Return boolean value deping on mouse position, if it is in circle or not
        if hypot((mouse_x - self.x), (mouse_y - self.y)) < self.radius:
            return True
        return False

    def stateControl(self, state):
        # -- Neutral or default state with no form of mouse selection
        if state == "neutral":
            self.color = defaultColor
            self.isSelected = False
        # -- Hovered state if mouse is hovering over circle object
        if state == "hovered":
            self.color = hoverColor
        # -- Selected state if mouse click UP on a "clicked" object
        if state == "selected":
            self.color = clickColor
            self.isSelected = True


    # Function to draw circle onto display
    def drawCircle(self, win):
        pg.draw.circle(win, self.color, (int(self.x), int(self.y)), self.radius)
    
    # checks for and handles collisions with walls and other balls
    def detectCollision(self, targets, distractors):

        # master list of targets and distractors
        masterList = targets + distractors

        # handles boundary collisions
        def handleBoundaryCollisions():
            if self.x - self.radius <= boundaries["left"]:
                self.dx = abs(self.dx)
                self.x = boundaries["left"] + self.radius
            if self.x + self.radius >= boundaries["right"]:
                self.dx = -abs(self.dx)
                self.x = boundaries["right"] - self.radius
            if self.y - self.radius <= boundaries["top"]: 
                self.dy = abs(self.dy)
                self.y = boundaries["top"] + self.radius
            if self.y + self.radius >= boundaries["bottom"]:
                self.dy = -abs(self.dy)
                self.y = boundaries["bottom"] - self.radius

        subSteps = 4  # Number of sub-steps per frame

        # Sub-stepping logic
        for _ in range(subSteps):
            self.x += self.dx / subSteps
            self.y += self.dy / subSteps
            handleBoundaryCollisions()

        # Handle two balls colliding by running final velocities function
        used = set({self})
        for a in masterList:
            if a not in used:
                if hypot(a.x - self.x, a.y - self.y) <= (a.radius + self.radius):
                    
                    # Collision math based on physics type
                    if exactPhysicsEnabled:
                        finalVelocitiesExact(self, a)
                    else:
                        finalVelocitiesOriginal(self, a)
                    
                    used.update({a})
            
        # Apply sub-stepping again after collisions
        for _ in range(subSteps):
            self.x += self.dx / subSteps
            self.y += self.dy / subSteps
            handleBoundaryCollisions()



    # get initial dx and dy values for a ball
    def velocity(self, game):

        velocity = game["speed"] * velocityFactor

        # randomly select a velocity for x direction
        dx = choice([-1,1]) * uniform(0, velocity)

        # calculate the velocity for y direction based on overall velocity and the x velocity we chose
        dy = choice([-1,1]) * sqrt((velocity ** 2) - (dx ** 2))

        return dx, dy

    # randomly shuffles the position of the balls
    def shufflePosition(self):
        self.x = choice(range(int(boundaries["left"] + self.radius) + 2, int(boundaries["right"] - self.radius) - 2))
        self.y = choice(range(int(boundaries["top"] + self.radius) + 2, int(boundaries["bottom"] - self.radius) - 2))


# checks that balls do not overlap, fixes problem if it occurs
# this is only called at the beginning of a trial, to ensure proper initial placement of balls
def getValidPositions(targets, distractors):

    # master list of all of the balls
    masterList = targets + distractors

    # stores the center of each placed ball to ensure they do not overlap
    placedBalls = []

    # shuffle each ball
    for ball in masterList:

        validPostion = False
        while not validPostion:

            # shuffle the position
            ball.shufflePosition()
            
            # assume the position is valid until proven otherwise
            validPostion = True

            # ensure the new ball does not overlap with other placed balls
            for placedBall in placedBalls:
                distanceFromBall = hypot(ball.x - placedBall.x, ball.y - placedBall.y)
                if distanceFromBall <= (2 * ball.radius) + 1:
                    validPostion = False
                    break
            
            # ensure ball does not overlap with fixation cross
            distanceFromCenter = hypot(ball.x  - (winWidth // 2), ball.y - (winHeight // 2)) - ball.radius
            if distanceFromCenter <= hypot(fixationCrossLength + 2, fixationCrossLength + 2):
                validPostion = False
            
            # if the position remained valid, then append this ball to the list of placed balls
            if validPostion:
                placedBalls.append(ball)

# function to handle ball collisions and calculate the final velocities after the collision
def finalVelocitiesOriginal(ball1, ball2):
    
    # Calculate initial speeds
    ball1InitialSpeed = sqrt(ball1.dx**2 + ball1.dy**2)
    ball2InitialSpeed = sqrt(ball2.dx**2 + ball2.dy**2)

    # Calculate relative position and velocity
    relativeXPosition = ball2.x - ball1.x
    relativeYPosition = ball2.y - ball1.y
    dx = ball2.dx - ball1.dx
    dy = ball2.dy - ball1.dy

    # Calculate dot product
    dotProduct = (relativeXPosition * dx) + (relativeYPosition * dy)

    # If dot product is greater than zero, balls are moving apart
    if dotProduct > 0:
        return

    # Calculate collision normal
    distance = hypot(relativeXPosition, relativeYPosition)
    if distance == 0:  # Avoid division by zero
        return
    normalX = relativeXPosition / distance
    normalY = relativeYPosition / distance

    # Calculate relative velocity along normal vector
    normalVelocity = (dx * normalX) + (dy * normalY)

    # Calculate impulse
    impulse = 2 * normalVelocity

    # Apply impulse to both objects (assuming equal mass)
    ball1.dx += impulse * normalX
    ball1.dy += impulse * normalY
    ball2.dx -= impulse * normalX
    ball2.dy -= impulse * normalY

    # Normalize velocities to maintain original speeds
    ball1NewSpeed = sqrt(ball1.dx ** 2 + ball1.dy ** 2)
    ball2NewSpeed = sqrt(ball2.dx ** 2 + ball2.dy ** 2)
    
    if ball1NewSpeed > 0:
        ball1.dx *= ball1InitialSpeed / ball1NewSpeed
        ball1.dy *= ball1InitialSpeed / ball1NewSpeed
    
    if ball2NewSpeed > 0:
        ball2.dx *= ball2InitialSpeed / ball2NewSpeed
        ball2.dy *= ball2InitialSpeed / ball2NewSpeed
    
    return

# simulates a perfectly elastic collision
def finalVelocitiesExact(ball1, ball2):

    # direction of impact
    normalVector = (ball2.x - ball1.x, ball2.y - ball1.y)

    # get unit normal vector and normal tangent vector
    magnitudeNormalVector = sqrt((normalVector[0] ** 2) + (normalVector[1] ** 2))
    unitNormal = (normalVector[0] / magnitudeNormalVector, normalVector[1] / magnitudeNormalVector)
    unitTangent = (-1 * unitNormal[1], unitNormal[0])

    # initial velocities for each ball as a vector
    ball1Velocities = (ball1.dx, ball1.dy)
    ball2Velocities = (ball2.dx, ball2.dy)

    # total velocity magnitude for scaling (floating point arithmetic errors)
    # this is just total kinetic energy but masses are equal and lets say equal 1
    # Calculate kinetic energy before collision
    initialKineticEnergy = 0.5 * (dotProduct(ball1Velocities, ball1Velocities) + dotProduct(ball2Velocities, ball2Velocities))


    # get final velocities for each ball in normal directions
    ball1NormalFinal = (dotProduct(ball2Velocities, unitNormal) * unitNormal[0], dotProduct(ball2Velocities, unitNormal) * unitNormal[1])
    ball2NormalFinal = (dotProduct(ball1Velocities, unitNormal) * unitNormal[0], dotProduct(ball1Velocities, unitNormal) * unitNormal[1])

    # get final velocities for each ball in tangential directions
    ball1TangentialFinal = (dotProduct(ball1Velocities, unitTangent) * unitTangent[0], dotProduct(ball1Velocities, unitTangent) * unitTangent[1])
    ball2TangentialFinal = (dotProduct(ball2Velocities, unitTangent) * unitTangent[0], dotProduct(ball2Velocities, unitTangent) * unitTangent[1])


    # update each ball with their new velocities
    finalBall1dx = ball1NormalFinal[0] + ball1TangentialFinal[0]
    finalBall1dy = ball1NormalFinal[1] + ball1TangentialFinal[1]
    finalBall2dx = ball2NormalFinal[0] + ball2TangentialFinal[0]
    finalBall2dy = ball2NormalFinal[1] + ball2TangentialFinal[1]

    # Calculate kinetic energy after collision
    finalKineticEnergy = 0.5 * ((finalBall1dx**2 + finalBall1dy**2) + (finalBall2dx**2 + finalBall2dy**2))

    # Scale factor based on kinetic energy preservation
    scaleFactor = sqrt(initialKineticEnergy / finalKineticEnergy) if finalKineticEnergy > 0 else 1

    ball1.dx = scaleFactor * finalBall1dx
    ball1.dy = scaleFactor * finalBall1dy
    ball2.dx = scaleFactor * finalBall2dx
    ball2.dy = scaleFactor * finalBall2dy

    return

# calculate the dot product of 2 2d vectors
def dotProduct(vector1, vector2):
    return (vector1[0] * vector2[0]) + (vector1[1] * vector2[1])

  



