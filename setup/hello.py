mport sys
import json

def main():
    # Claire passes data as a JSON string in the first argument
    try:
        args = json.loads(sys.argv[1])
        name = args.get("name", "Stranger")
        greeting = args.get("greeting", "Hello")
        
        result = {"message": f"{greeting}, {name}! Your test is working."}
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
