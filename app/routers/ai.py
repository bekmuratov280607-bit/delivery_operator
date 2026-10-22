
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.database import get_db
from app.models import Order, Product
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def get_context(
    order_id: int | None,
    facts: str,
    db: Session,
) -> str:
    # Базадан акыркы 100 товарды алуу
    products = (
        db.query(Product)
        .order_by(Product.id.desc())
        .limit(100)
        .all()
    )

    product_lines = [
        (
            f"id={p.id}; "
            f"name={p.product_name}; "
            f"price={p.price}; "
            f"stock={p.stock}; "
            f"description={p.description}"
        )
        for p in products
    ]

    order_text = "Заказ ID берилген жок."

    # Эгер заказ ID берилсе, анын маалыматын алуу
    if order_id is not None:
        order = db.get(Order, order_id)

        if order:
            product = db.get(Product, order.product_id)

            order_text = (
                f"Заказ ID={order.id}; "
                f"статус={order.order_status}; "
                f"товар={product.product_name if product else 'unknown'}; "
                f"саны={order.quantity}; "
                f"сумма={order.total_price}; "
                f"дарек={order.address}"
            )
        else:
            order_text = (
                f"{order_id} ID менен заказ табылган жок."
            )

    return (
        "Товарлар базасы:\n"
        + ("\n".join(product_lines) or "Базада товар жок.")
        + "\n\nЗаказ маалыматы:\n"
        + order_text
        + "\n\nКошумча фактылар:\n"
        + (facts or "Кошумча фактылар берилген жок.")
    )


def is_temporary_error(exc: Exception) -> bool:
    status = (
        getattr(exc, "code", None)
        or getattr(exc, "status_code", None)
    )

    if status in (429, 500, 502, 503, 504):
        return True

    message = str(exc).lower()

    temporary_terms = (
        "503",
        "unavailable",
        "high demand",
        "429",
        "resource_exhausted",
        "rate limit",
        "internal server error",
        "deadline exceeded",
        "timed out",
        "timeout",
        "502",
        "504",
    )

    return any(term in message for term in temporary_terms)


def ask_gemini(
    data: ChatRequest,
    db: Session,
) -> ChatResponse:
    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "your_gemini_api_key_here"
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini API ачкычы коюлган эмес. "
                ".env файлын текшер."
            ),
        )

    # База жана фактылар боюнча контекст
    context = get_context(
        order_id=getattr(data, "order_id", None),
        facts=data.facts,
        db=db,
    )

    prompt = f"""
Сен Glovo сыяктуу жеткирүү кызматындагы колдоо жардамчысысың.

Колдонуучунун суроосуна анын тилинде жооп бер.

ЭРЕЖЕЛЕР:
1. Товардын баасын жана бар-жогун базадагы маалыматтан гана айт.
2. Базада жок товарды бар деп ойлоп таппа.
3. Заказдын статусун ойлоп таппа.
4. Курьердин GPS жайгашкан жери же келүү убактысы берилбесе,
   аны билем деп айтпа.
5. Кошумча фактыларды эске ал, бирок аларды берилген маалымат
   катары гана колдон.
6. Кыска, сылык жана түшүнүктүү жооп бер.
7. Колдонуучуга кийинки кадамды сунушта.
8. Заказды өзүң өзгөрттүм же курьер менен байланыштым деп айтпа.

БАЗАДАН АЛЫНГАН КОНТЕКСТ:
{context}

КОЛДОНУУЧУНУН СУРООСУ:
{data.text}
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Жалпы 3 аракет: биринчи аракет + 2 кайталоо
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                    ),
                )

                answer_text = (response.text or "").strip()

                if not answer_text:
                    raise HTTPException(
                        status_code=502,
                        detail="Gemini бош жооп берди.",
                    )

                return ChatResponse(
                    answer=answer_text,
                    source="gemini",
                )

            except HTTPException:
                raise

            except Exception as exc:
                if not is_temporary_error(exc):
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            "Gemini менен байланышта ката чыкты. "
                            "Моделдин атын, API ачкычын жана "
                            "Google AI Studio мүмкүнчүлүгүн текшер."
                        ),
                    ) from exc

                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Gemini азыр убактылуу жеткиликсиз. "
                        "Бир аздан кийин кайра аракет кыл."
                    ),
                ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI кызматын иштетүүдө ката чыкты.",
        ) from exc

    raise HTTPException(
        status_code=503,
        detail="Gemini азыр жооп бере албай жатат.",
    )


@router.post("/answer/", response_model=ChatResponse)
def answer(
    data: ChatRequest,
    db: Session = Depends(get_db),
):
    return ask_gemini(data, db)


@router.post("/analysis/", response_model=ChatResponse)
def analyze(
    data: ChatRequest,
    db: Session = Depends(get_db),
):
    return ask_gemini(data, db)
