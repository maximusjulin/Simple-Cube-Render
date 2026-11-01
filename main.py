import numpy as np
import pygame

screenWidth = 800
screenHeight = 600

def cubeVerticesHomogeneous(size):
    ## hSize is half of the length of a cube, as all the points are half the length away from the center
    ## in every axis.
    hSize = size / 2.0
    ##Vertices are the homogeneous coordinates of the 8 corners, representing (x,y,z,d) where d starts as 1
    vertices = np.array([
        [-hSize, -hSize, -hSize, 1.0],
        [ hSize, -hSize, -hSize, 1.0],
        [ hSize,  hSize, -hSize, 1.0],
        [-hSize,  hSize, -hSize, 1.0],
        [-hSize, -hSize,  hSize, 1.0],
        [ hSize, -hSize,  hSize, 1.0],
        [ hSize,  hSize,  hSize, 1.0],
        [-hSize,  hSize,  hSize, 1.0],
    ])
    ##Edges are defined as two vertex indices, which make up the 12 edges of the cube
    edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ]
    return vertices, edges

def scaleVertices(vertices, scaleFactor):
    scale_matrix = np.array([
        [scaleFactor, 0, 0, 0],
        [0, scaleFactor, 0, 0],
        [0, 0, scaleFactor, 0],
        [0, 0, 0, 1]
    ])
    return vertices @ scale_matrix

def rotateYMatrix(angle):
    cos, sin = np.cos(angle), np.sin(angle)
    rotation_matrix = np.array([
        [ cos, 0,  sin, 0],
        [  0, 1,   0, 0],
        [-sin, 0,  cos, 0],
        [  0, 0,   0, 1]
    ])
    return rotation_matrix

def rotateXMatrix(angle):
    cos, sin = np.cos(angle), np.sin(angle)
    rotation_matrix = np.array([
        [1, 0, 0, 0],
        [0, cos,-sin, 0],
        [0, sin, cos, 0],
        [0, 0, 0, 1]
    ])
    return rotation_matrix

def rotateZMatrix(angle):
    cos, sin = np.cos(angle), np.sin(angle)
    rotation_matrix = np.array([
        [cos, -sin, 0, 0],
        [sin,  cos, 0, 0],
        [0,    0,   1, 0],
        [0,    0,   0, 1]
    ])
    return rotation_matrix

#Given field of view in radians, aspect ratio, near and far plane distances,
#return the projection matrix, which creates the realistic 3D to 2D perspective effect
def projectionMatrix(fov, aspect_ratio, near, far):
    f = 1.0 / np.tan(fov / 2.0)
    q = far / (far - near)
    projection_matrix = np.array([
        [f / aspect_ratio, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, q, -near * q],
        [0, 0, 1, 0]
    ])
    return projection_matrix

def viewMatrix(camera, yaw, pitch):
    cosy, siny = np.cos(yaw), np.sin(yaw)
    cosp, sinp = np.cos(pitch), np.sin(pitch)
    ## calculate rotation matrices
    rotation_yaw = np.array([
        [ cosy, 0, siny, 0],
        [  0, 1,  0, 0],
        [-siny, 0, cosy, 0],
        [  0, 0,  0, 1]
    ])
    rotation_pitch = np.array([
        [1,   0,    0, 0],
        [0,  cosp, -sinp, 0],
        [0,  sinp,  cosp, 0],
        [0,    0,    0, 1]
    ])
    ## calculate translation matrix
    translation = np.array([
        [1, 0, 0, -camera[0]],
        [0, 1, 0, -camera[1]],
        [0, 0, 1, -camera[2]],
        [0, 0, 0, 1]
    ])
    ## Combine rotation and translation
    return rotation_pitch @ rotation_yaw @ translation

def matrixMultiplicaton(vertices, objectRotationMatrix, viewCamMatrix, projMatrix):
    ## The big calculation!
    ## M_vertices @ (Projection Matrix @ View Camera Matrix @ Object Rotation Matrix)^T
    coordinates = vertices @ (projMatrix @ viewCamMatrix @ objectRotationMatrix).T
    depth = coordinates[:, 3:4]
    ## If depth is very small, we avoid division by zero
    mask = depth > 0.001
    ## create zero matrix with same shape as coordinates
    ndc_coords = np.zeros_like(coordinates)
    ## only divide where we have an approved depth
    ndc_coords[mask[:, 0]] = coordinates[mask[:, 0]] / depth[mask[:, 0]]
    
    x = (ndc_coords[:, 0] + 1) * 0.5 * screenWidth
    y = (1 - (ndc_coords[:, 1] + 1) * 0.5) * screenHeight

    projected = []
    for i in range(vertices.shape[0]):
        ## if the point is in front of camera, add to list
        if mask[i, 0]:
            projected.append((int(x[i]), int(y[i])))
        ## since behind camera, add None as the camera cannot see it
        else:
            projected.append(None)
    return projected

def render3dTo2d(screen, projected, edges):
    ## Draw Edges
    for edge in edges:
        start_pos = projected[edge[0]]
        end_pos = projected[edge[1]]
        if start_pos is None or end_pos is None:
            continue
        pygame.draw.line(screen, (255, 255, 255), start_pos, end_pos, 2)
    ## Draw Vertices
    for _, vertex in enumerate(projected):
        if vertex is None:
            continue
        pygame.draw.circle(screen, (250, 0, 0), vertex, 5)

## Pygame Initialization for rendering
pygame.init()
screen = pygame.display.set_mode((screenWidth, screenHeight))

pygame.display.set_caption("21241 Project - 3D Cube Rotation")
clock = pygame.time.Clock()

keysHolding = {}
toggleSpinX, toggleSpinY, toggleSpinZ = False, False, False

## Main render loop
vertices, edges = cubeVerticesHomogeneous(100)
camera = np.array([0.0, 0.0, -300.0])
yaw, pitch = 0.0, 0.0
objectRotationMatrix = np.identity(4)

running = True
while running:
    dt = clock.tick(60)
    ## Control Keypresses
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_x:
                toggleSpinX = not toggleSpinX
            elif event.key == pygame.K_y:
                toggleSpinY = not toggleSpinY
            elif event.key == pygame.K_z:
                toggleSpinZ = not toggleSpinZ
            elif event.key not in keysHolding:
                keysHolding[event.key] = True
        for key in keysHolding:
            if key == pygame.K_w:
                camera[2] += 10.0
            if key == pygame.K_s:
                camera[2] -= 10.0
            if key == pygame.K_a:
                camera[0] -= 10.0
            if key == pygame.K_d:
                camera[0] += 10.0
            if key == pygame.K_q:
                camera[1] += 10.0
            if key == pygame.K_e:
                camera[1] -= 10.0
            if key == pygame.K_UP:
                pitch += 0.1
            if key == pygame.K_DOWN:
                pitch -= 0.1
            if key == pygame.K_LEFT:
                yaw -= 0.1
            if key == pygame.K_RIGHT:
                yaw += 0.1
            if key == pygame.K_r:
                vertices = scaleVertices(vertices, 1.1)
            if key == pygame.K_t:
                vertices = scaleVertices(vertices, 0.9)
        if event.type == pygame.KEYUP:
            if event.key in keysHolding:
                del keysHolding[event.key]
    ## Make screen black
    screen.fill((0, 0, 0))
    
    ## Depending on toggles, rotate the object
    if toggleSpinX:
        objectRotationMatrix = objectRotationMatrix @ rotateXMatrix(0.1)
    if toggleSpinY:
        objectRotationMatrix = objectRotationMatrix @ rotateYMatrix(0.1)
    if toggleSpinZ:
        objectRotationMatrix = objectRotationMatrix @ rotateZMatrix(0.1)
    ## get the view camera matrix, given the camera and its orientation
    viewCamMatrix = viewMatrix(camera, yaw, pitch)
    ## get the projection matrix
    projMatrix = projectionMatrix(np.radians(90), screenWidth / screenHeight, 0.1, 1000.0)
    
    ## get the projected 2D points from the matrix multiplications, filtering out points behind the camera
    projected = matrixMultiplicaton(vertices, objectRotationMatrix, viewCamMatrix, projMatrix)
    
    ## Render the projected 2D points and edges on the screen
    render3dTo2d(screen, projected, edges)
    pygame.display.flip()

pygame.quit()