export interface ToolRow {
  id: string
  tool: 'tyre_semantic_search' | 'product_description' | 'landing_price' | string
  label: string
  status: 'pending' | 'done'
}

export type ChatMessage =
  | { kind: 'user';   id: string; content: string }
  | { kind: 'tools';  id: string; rows: ToolRow[]; collapsed: boolean }
  | { kind: 'answer'; id: string; content: string }
  | { kind: 'error';  id: string; message: string }
