from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter()

@router.get("/asr/ws")
async def websocket_docs():
    return JSONResponse({
        "description": "WebSocket Streaming Interface",
        "endpoint": "wss://{server_url}/ws/{type} or wss://{server_url}/ws",
        "protocol": "WebSocket",
        "type": "msgpack or json (default: msgpack)",
        "send_format": {
            "refer": {
                "description": "오디오 임베딩 벡터 전송",
                "byte_structure": {
                    "dict": {
                        "type": "refer",
                        "groupId": "str - 그룹 단위 연결 키",
                    },
                    "embedding_metadata": {
                        "userId": "int - 오디오 임벧딩 데이터 개수",
                        " ... " : " ... "
                    },
                    "embedding": [
                        "임베딩 벡터 데이터", " ... "
                    ]
                },
            },
            "metadata": {
                "description": "메타데이터 전송",
                "byte_structure": {
                    "dict": {
                        "type": "metadata",
                        "userId": "str - 사용자 단위 키",
                        "groupId": "str - 그룹 단위 연결 키",
                    },
                    "metadata": {
                        "agenda": ["str - 아젠다", " ... "],
                        "num_people": "int - 화자 수",
                        "meeting_topic": "str - 회의 주제",
                    },
                },
            },
            "diarized": {
                "description": "음성인식 및 화자분리 요청",
                "byte_structure": {
                    "dict": {
                        "type": "diarized",
                        "userId": "str - 사용자 단위 키",
                        "groupId": "str - 그룹 단위 연결 키",
                    },
                    "audio": "오디오 데이터"
                },
            },
            "context": {
                "description": "LLM 요약 요청",
                "byte_structure": {
                    "dict": {
                        "type": "context",
                        "groupId": "str - 그룹 단위 연결 키",
                    },
                },
            },
            "context_done" : {
                "description": "LLM 요청 및 기존 데이터 정리",
                "byte_structure": {
                    "dict": {
                        "type": "context_done",
                        "groupId": "str - 그룹 단위 연결 키",
                    },
                },
            }
        },
        "receive_format": {
            "refer": "응답 없음",
            "metadata": "응답 없음",
            "diarized": {
                "completed": [
                    {
                        "order": "int - 발화 순서",
                        "lang": ["str - 인식된 언어", " ... "],
                        "text": "str - 인식된 텍스트",
                        "words": [
                            {
                                "start": "float - 시작 시간",
                                "end": "float - 종료 시간",
                                "text": "str - 인식된 단어",
                                "lang": "str - 인식된 언어",
                            },
                            {
                                " ... ": " ... "
                            }
                        ],
                        "user_id": "str - 화자 ID",
                        "audio_id": "str - 오디오를 녹음한 사용자 ID",
                    }
                ],
                "candidate": "completed와 동일한 구조이나, 인식된 텍스트가 불완전함",
            },
            "context": {
                "context": "str - LLM 요약 결과",
                "agenda": ["int - 완료한 아젠다 index", " ... "],
                "feedback": {
                    "user_id": "str - 피드백 내용",
                }
            }
        },
        "flow": [
            "1. 클라이언트가 WebSocket 연결",
            "2. 클라이언트가 refer을 통해 오디오 임베딩 벡터 전송",
            "3. 클라이언트가 metadata를 통해 메타데이터 전송",
            "4. 클라이언트가 diarized를 통해 음성인식 및 화자분리 요청",
            "5. 서버는 음성인식 및 화자분리 진행",
            "6. 서버는 음성인식 및 화자분리 결과를 실시간으로 클라이언트에 반환",
            "7. 클라이언트가 context를 통해 LLM 요약 요청",
            "8. 서버는 LLM 요약 진행",
            "9. 서버는 LLM 요약 결과를 클라이언트에 반환",
            "10. 클라이언트가 context_done을 통해 LLM 요청 및 기존 데이터 정리",
            "11. 서버는 LLM 요청 및 기존 데이터 정리 진행",
            "12. 서버는 LLM 요청 및 기존 데이터 정리 결과를 클라이언트에 반환",
            "13. 해당 groupId에 대한 요청 종료",
            "14. 클라이언트 요청 종료시, 따로 플래그 없이 연결 종료 하면 됨"
        ],
    })

__all__ = ["router"]
