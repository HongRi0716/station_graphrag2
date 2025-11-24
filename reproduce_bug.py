
import base64
from dataclasses import dataclass
from typing import Any, Dict, List
import json

@dataclass
class AssetBinPart:
    data: bytes
    mime_type: str

class ParsedDocumentData:
    def _serialize_doc_parts(self, doc_parts: List[Any]) -> List[Dict[str, Any]]:
        serialized_parts = []
        for part in doc_parts:
            part_dict = {}
            for key, value in part.__dict__.items():
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    part_dict[key] = value
                elif isinstance(value, bytes):
                    # Serialize bytes to base64
                    part_dict[key] = {"__type__": "bytes", "data": base64.b64encode(value).decode("utf-8")}
                else:
                    part_dict[key] = str(value)
            part_dict["_type"] = part.__class__.__name__
            serialized_parts.append(part_dict)
        return serialized_parts

    def _deserialize_doc_parts(self, serialized_parts: List[Dict[str, Any]]) -> List[Any]:
        deserialized_parts = []
        for part_dict in serialized_parts:
            processed_dict = {}
            for k, v in part_dict.items():
                if isinstance(v, dict) and v.get("__type__") == "bytes":
                    try:
                        processed_dict[k] = base64.b64decode(v["data"])
                    except Exception:
                        processed_dict[k] = v
                else:
                    processed_dict[k] = v
            
            part_obj = type("DocumentPart", (), processed_dict)()
            deserialized_parts.append(part_obj)
        return deserialized_parts

def test_serialization():
    original_data = b"hello world"
    part = AssetBinPart(data=original_data, mime_type="image/png")
    
    serializer = ParsedDocumentData()
    serialized = serializer._serialize_doc_parts([part])
    
    print(f"Serialized data: {serialized[0]['data']}")
    print(f"Type of serialized data: {type(serialized[0]['data'])}")
    
    deserialized = serializer._deserialize_doc_parts(serialized)
    restored_part = deserialized[0]
    
    print(f"Restored data: {restored_part.data}")
    print(f"Type of restored data: {type(restored_part.data)}")
    
    try:
        encoded = base64.b64encode(restored_part.data)
        print(f"base64 encoding successful: {encoded}")
        assert restored_part.data == original_data
        print("Data integrity check passed")
    except Exception as e:
        print(f"base64 encoding failed: {e}")

if __name__ == "__main__":
    test_serialization()
