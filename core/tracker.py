import numpy as np
from collections import OrderedDict
import config

class CentroidTracker:
    def __init__(self):
        # The next available ID number
        self.nextObjectID = 0
        
        # Dictionary to store current center x,y: {ID: (x, y)}
        self.objects = OrderedDict()
        
        # Dictionary to store number of consecutive frames this ID was lost
        self.disappeared = OrderedDict()
        
        # Dictionary to store the bounding box: {ID: (x1, y1, x2, y2)}
        self.bboxes = OrderedDict()

        # History for trails and stability: {ID: [(x,y), (x,y)...]}
        self.history = OrderedDict()

    def register(self, centroid, box):
        """Register a new object ID"""
        self.objects[self.nextObjectID] = centroid
        self.bboxes[self.nextObjectID] = box
        self.disappeared[self.nextObjectID] = 0
        self.history[self.nextObjectID] = [centroid]
        self.nextObjectID += 1

    def deregister(self, objectID):
        """Remove an ID from tracking"""
        del self.objects[objectID]
        del self.disappeared[objectID]
        del self.bboxes[objectID]
        del self.history[objectID]

    def update(self, rects):
        """
        Input: list of bounding boxes from YOLO [x1, y1, x2, y2]
        Output: Dictionary of objects and their data
        """
        # If no boxes detected...
        if len(rects) == 0:
            # Mark existing objects as disappeared
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > config.MAX_DISAPPEARED_FRAMES:
                    self.deregister(objectID)
            return self.objects

        # Calculate centroids for input rects
        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        # If we have no existing objects, register all inputs
        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], rects[i])

        # Otherwise, match inputs to existing objects
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            # Calculate distances between all inputs and all existing objects
            # Using NumPy broadcasting for efficiency
            D = np.linalg.norm(np.array(objectCentroids)[:, np.newaxis] - inputCentroids, axis=2)

            # Find the smallest value in each row (closest match)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue

                # Verify the distance is within our limit
                if D[row, col] > config.MAX_TRACKING_DISTANCE:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.bboxes[objectID] = rects[col]
                self.disappeared[objectID] = 0
                
                # Update history for trails/stability
                self.history[objectID].append(inputCentroids[col])
                # Limit history size
                if len(self.history[objectID]) > config.STABILITY_HISTORY_LEN:
                    self.history[objectID].pop(0)

                usedRows.add(row)
                usedCols.add(col)

            # Deal with disappearances
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            for row in unusedRows:
                objectID = objectIDs[row]
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > config.MAX_DISAPPEARED_FRAMES:
                    self.deregister(objectID)

            # Deal with new objects
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)
            for col in unusedCols:
                self.register(inputCentroids[col], rects[col])

        return self.objects