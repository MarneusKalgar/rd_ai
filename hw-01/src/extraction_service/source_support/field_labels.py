"""Declared neutral-cell vocabulary for the field-role development experiment."""

from typing import Final

PRODUCT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Description",
        "제품명",
        "Descrizione",
        "Megnevezés",
        "Omschrijving",
        "Nume produs",
        "Descripción",
        "产品名称",
    }
)
BUYER_CODES: Final[frozenset[str]] = frozenset(
    {"Buyer product code", "Buyer product ID", "Customer item number"}
)
OTHER_CODES: Final[frozenset[str]] = frozenset(
    {
        "Article code",
        "제품 코드",
        "Codice prodotto",
        "Termék kódja",
        "Artikelcode",
        "Cod produs",
        "Código artículo",
        "产品代码",
        "Supplier product code",
        "Barcode",
    }
)
DELIVERY_DATES: Final[frozenset[str]] = frozenset(
    {"Delivery date", "Requested delivery date", "납기요청일", "交货日期"}
)
CONTEXT_DATES: Final[frozenset[str]] = frozenset({"Service date"})
OTHER_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "Order date",
        "Buyer",
        "Ship to",
        "Payment terms",
        "Currency",
        "Quantity",
        "UOM",
        "Unit price",
        "PO number",
        "Line no.",
        "발주번호",
        "발주일자",
        "발주처",
        "배송처",
        "주문수량",
        "단위",
        "행 번호",
        "Numero ordine",
        "Data ordine",
        "Cliente",
        "Indirizzo di consegna",
        "Valuta",
        "Quantità",
        "Unità",
        "Megrendelés dátuma",
        "Ügyfél neve",
        "Szállítási cím",
        "Fizetési feltétel",
        "A rendelés összértéke",
        "Rendelt mennyiség",
        "Mértékegység",
        "Ár",
        "PO nummer",
        "Order datum",
        "Leveradres",
        "Aantal",
        "Eenheid",
        "Data emiterii comenzii",
        "Firma",
        "Moneda",
        "Valoare comandă fără TVA",
        "Comanda",
        "Unitate",
        "Preț unitar",
        "Fecha pedido",
        "Nombre del cliente",
        "Cantidad",
        "Unidad",
        "合同号",
        "开单日期",
        "采购方",
        "付款方式",
        "币种",
        "订购数量",
        "单位",
        "单价",
        "序号",
    }
)
KNOWN_FIELDS: Final[frozenset[str]] = (
    PRODUCT_NAMES | BUYER_CODES | OTHER_CODES | DELIVERY_DATES | CONTEXT_DATES | OTHER_FIELDS
)
