from pydantic import BaseModel, Field


class GetTyreDescriptionArgs(BaseModel):
    sku: str = Field(..., description="The SKU Code of the tyre for which the Tyre Description is needed. Eg: 100227")


class GetLandingPriceArgs(BaseModel):
    sku: str = Field(..., description="The SKU Code of the tyre for which the Tyre Landing Price is needed. Eg: 100227")


class GetTyreSizeSearchArgs(BaseModel):
    size: str = Field(
        ...,
        description=(
            "The tyre size to search for. Accepts conventional (e.g. '2.75-18', '3.00-17') "
            "or metric formats (e.g. '80/100-18', '100/90-17'). "
            "Use only the size portion, not the full description."
        ),
    )


class GetSemanticQueryArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Natural language description of the vehicle for which tyres are sought. "
            "Include brand, model, and variant if known. Eg: 'Hero Splendor 100cc tyres', "
            "'Honda Shine 125cc front tyre'"
        ),
    )


tyre_size_search_tool = {
    'type': 'function',
    'function': {
        'name': 'tyre_size_search',
        'description': (
            'Finds all CEAT tyre SKUs available in a given size. '
            'Use when the user asks what tyres are available in a specific size '
            '(e.g. "2.75-18", "80/100-18") regardless of vehicle. '
            'Returns SKU, full description, and landing price for each match.'
        ),
        'parameters': GetTyreSizeSearchArgs.model_json_schema(),
    },
}

landing_price_tool = {
    'type': 'function',
    'function': {
        'name': 'landing_price',
        'description': 'Returns the NBP and calculated landing price for a given tyre SKU.',
        'parameters': GetLandingPriceArgs.model_json_schema(),
    },
}

tyre_description_tool = {
    'type': 'function',
    'function': {
        'name': 'product_description',
        'description': 'Returns the material description and pricing details for a given tyre SKU.',
        'parameters': GetTyreDescriptionArgs.model_json_schema(),
    },
}

semantic_search_tool = {
    'type': 'function',
    'function': {
        'name': 'tyre_semantic_search',
        'description': (
            'Searches the tyre-vehicle mapping catalogue using semantic similarity. '
            'Returns the top 5 most relevant chunks containing vehicle brand, model, variant, '
            'tyre position (Front/Rear), recommended SKU, and tyre name. '
            'Call this first to find candidate SKUs before calling landing_price or product_description.'
        ),
        'parameters': GetSemanticQueryArgs.model_json_schema(),
    },
}