from pydantic import BaseModel, Field


class GetTyreDescriptionArgs(BaseModel):
    sku: str = Field(..., description="The SKU Code of the tyre for which the Tyre Description is needed. Eg: 100227")


class GetLandingPriceArgs(BaseModel):
    sku: str = Field(..., description="The SKU Code of the tyre for which the Tyre Landing Price is needed. Eg: 100227")


class GetSemanticQueryArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Natural language description of the vehicle for which tyres are sought. "
            "Include brand, model, and variant if known. Eg: 'Hero Splendor 100cc tyres', "
            "'Honda Shine 125cc front tyre'"
        ),
    )


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