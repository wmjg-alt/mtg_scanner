import numpy as np
from collections import OrderedDict
import config
from data.stats_manager import StatsManager

class CentroidTracker:
    def __init__(self):
        self.stats = StatsManager()
        self.nextObjectID = self.stats.generate_id() # Random Start
        
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.bboxes = OrderedDict()
        self.history = OrderedDict()

    def register(self, centroid, box):
        # Use our Alphanumeric ID
        objectID = self.nextObjectID
        
        self.objects[objectID] = centroid
        self.bboxes[objectID] = box
        self.disappeared[objectID] = 0
        self.history[objectID] = [centroid]
        
        # Log it
        count = self.stats.increment_objects_seen()
        print(f"[Tracker] New Object: {objectID} (Total Seen: {count})")
        
        # Generate next ID
        self.nextObjectID = self.stats.generate_id()
        # Ensure uniqueness (simple check)
        while self.nextObjectID in self.objects:
            self.nextObjectID = self.stats.generate_id()

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]
        del self.bboxes[objectID]
        del self.history[objectID]

    def update(self, rects):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > config.MAX_DISAPPEARED_FRAMES:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], rects[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            # Distance Logic 
            D = np.linalg.norm(np.array(objectCentroids)[:, np.newaxis] - inputCentroids, axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols: continue
                if D[row, col] > config.MAX_TRACKING_DISTANCE: continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.bboxes[objectID] = rects[col]
                self.disappeared[objectID] = 0
                self.history[objectID].append(inputCentroids[col])
                if len(self.history[objectID]) > config.STABILITY_HISTORY_LEN:
                    self.history[objectID].pop(0)

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            for row in unusedRows:
                objectID = objectIDs[row]
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > config.MAX_DISAPPEARED_FRAMES:
                    self.deregister(objectID)

            unusedCols = set(range(0, D.shape[1])).difference(usedCols)
            for col in unusedCols:
                self.register(inputCentroids[col], rects[col])

        return self.objects