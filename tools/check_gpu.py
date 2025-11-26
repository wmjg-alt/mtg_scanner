import torch
import torchvision
import ultralytics

def check():
    print(f"--- GPU DIAGNOSTICS ---")
    print(f"Torch Version: {torch.__version__}")
    print(f"Torchvision Version: {torchvision.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
    else:
        print("WARNING: Running on CPU. FPS will be low.")

    try:
        # Test torchvision NMS (This is what crashed before)
        print("\nTesting Torchvision NMS on CUDA...")
        boxes = torch.tensor([[0, 0, 100, 100]], dtype=torch.float32).cuda()
        scores = torch.tensor([1.0], dtype=torch.float32).cuda()
        result = torchvision.ops.nms(boxes, scores, 0.5)
        print("SUCCESS: Torchvision NMS is working on GPU!")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    check()