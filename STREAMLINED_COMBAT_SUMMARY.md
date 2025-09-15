# Streamlined Combat System - Idle Duelist

## ✅ **Issues Fixed**

### 🐛 **1. Combat Crash Fixed**
**Problem**: `AttributeError: 'CombatScreen' object has no attribute 'current_turn_player'`

**Solution**: Added proper initialization of `current_turn_player` attribute in the `start_combat()` method:
```python
# Reset combat state
self.turn_order_set = False
self.turn_number = 1
self.current_turn_player = None  # ← Added this line
```

### 🎯 **2. Streamlined Combat UI**
**Problem**: Confusing combat interface with simulation button

**Solution**: Simplified to single, clear combat option:
- ❌ **Removed**: "Simulate Combat (Run 100 Test Fights)" button
- ✅ **Kept**: Single "Start Duel (Fight Random Opponent)" button
- ✅ **Enhanced**: Larger, more prominent duel button

## 🎮 **New Combat Experience**

### **Before**:
- Two buttons: "Quick Duel" + "Simulate Combat"
- Confusing options for players
- Simulation button cluttered the interface

### **After**:
- **Single clear option**: "⚔️ Start Duel (Fight Random Opponent)"
- **Streamlined flow**: Click → Queue → Fight → Complete
- **Turn-by-turn combat** with ability icons
- **Clean, focused interface**

## 🔧 **Technical Changes**

### **Files Modified**:
1. **`mobile_ui/screens/combat.py`**:
   - Fixed `current_turn_player` initialization
   - Removed `simulate_combat()` method entirely
   - Simplified combat options UI
   - Enhanced duel button styling

### **Key Improvements**:
- **Crash Prevention**: Proper attribute initialization
- **UI Simplification**: Single combat option
- **Better UX**: Clear, focused combat flow
- **Maintained Features**: Turn-by-turn combat with icons

## 🎯 **Combat Flow**

1. **Player goes to Combat screen**
2. **Clicks "Start Duel" button**
3. **System generates random opponent**
4. **Shows opponent info popup**
5. **Player clicks "Fight!"**
6. **Combat plays out turn-by-turn with ability icons**
7. **Shows winner and results**

## 🚀 **Ready for Testing**

The streamlined combat system is now running! Test it by:
1. Creating a player
2. Going to Combat screen
3. Clicking "Start Duel"
4. Watching the turn-by-turn combat with ability icons

All tests pass ✅ and the combat system is now crash-free and user-friendly!



