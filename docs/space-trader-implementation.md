# Space Trader Implementation Checklist

## Phase 0 - Asset Pipeline
- [x] Extract Palm PICT resources to PNG previews
- [x] Convert PNG to RGB565 `.raw` for Bit-Firmware
- [x] Generate `assets_manifest.json`
- [x] Sync assets into Bit-Firmware SPIFFS
- [ ] Validate missing IDs vs expected PICT list

## Phase 1 - Core Model + Persistence
- [ ] Finalize `SpaceTraderCore` data tables (ships, equipment, gadgets, quests)
- [ ] Add deterministic RNG wrapper for reproducibility
- [ ] Implement save/load payload (state, seed, quest flags)
- [ ] Wire save/load into Bit-Firmware storage

## Phase 2 - UI Framework for Space Trader
- [ ] Create `SpaceTraderGame` (Game subclass) scaffold
- [ ] Build shared UI layout helpers (list panels, tab bar, footer)
- [ ] Define screen enum and navigation stack
- [ ] Implement input focus model (D-pad + A/B + Menu)
- [ ] Implement text rendering and numeric formatting helpers

## Phase 3 - Core Screens (Docked)
- [ ] Main dock summary screen
- [ ] System Information screen
- [ ] Buy Cargo screen
- [ ] Sell Cargo screen
- [ ] Ship Yard screen
- [ ] Buy Fuel / Buy Repairs modal
- [ ] Bank screen (loan + payback)

## Phase 4 - Navigation Screens
- [ ] Galactic Chart (full map)
- [ ] Short Range Chart
- [ ] Warp Confirm screen
- [ ] Execute Warp flow

## Phase 5 - Encounters and Combat
- [ ] Encounter screen (text mode)
- [ ] Encounter screen (graphic mode)
- [ ] Attack/flee/surrender/bribe flows
- [ ] Plunder flow

## Phase 6 - Equipment and Crew
- [ ] Buy Equipment screen
- [ ] Sell Equipment screen
- [ ] Personnel roster
- [ ] Ship type info
- [ ] Trade-in ship flow

## Phase 7 - Quests and Special Events
- [ ] Quest list screen
- [ ] Special cargo screen
- [ ] Special event prompts
- [ ] Newspaper (headlines)

## Phase 8 - Endgame and Scores
- [ ] Retire screen
- [ ] Destroyed screen
- [ ] Utopia screen
- [ ] Final score calculation
- [ ] High score table integration

## Phase 9 - Integration and Polish
- [ ] GameRunner registration
- [ ] Main menu entry
- [ ] Splash screen entry
- [ ] Instructions entry
- [ ] LED mapping entry
- [ ] Performance profiling and memory budget pass
- [ ] QA pass on all flows
