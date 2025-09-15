# Idle Duelist - Mobile Testing Checklist

## 🎯 **Complete Testing Guide**

Use this checklist to test all buttons and mechanics in the mobile app to ensure nothing is missing.

### 📱 **Starting the Mobile App**

```bash
python mobile_app.py
```

The app should start at **375x667 resolution** (iPhone 6/7/8 standard) and display the main menu.

---

## 🏠 **Main Menu Screen Testing**

### ✅ **Title and Layout**
- [ ] App title "⚔️ Idle Duelist ⚔️" displays correctly
- [ ] Subtitle "Turn-based Combat RPG" shows
- [ ] Layout fits properly in portrait mode
- [ ] All text is readable and properly sized

### ✅ **Menu Buttons**
- [ ] **👤 Player Stats** - Navigate to stats screen
- [ ] **⚔️ Equipment** - Navigate to equipment screen  
- [ ] **🏛️ Faction & Abilities** - Navigate to faction screen
- [ ] **⚡ Duel** - Navigate to combat screen
- [ ] **⚙️ Settings** - Navigate to settings screen
- [ ] **➕ New Player** - Opens player creation popup

### ✅ **Status Display**
- [ ] Shows "👤 No Player" when no player exists
- [ ] Shows "🏛️ No Faction" when no player exists
- [ ] Shows "🏆 Victory Points: 0" when no player exists

---

## 👤 **Player Creation Testing**

### ✅ **New Player Popup**
- [ ] Popup opens when clicking "➕ New Player"
- [ ] Popup is properly sized for mobile (85% x 75%)
- [ ] Text input field for player name works
- [ ] Faction selection buttons display correctly
- [ ] All 3 factions show with descriptions:
  - [ ] Order of the Silver Crusade
  - [ ] Shadow Covenant  
  - [ ] Wilderness Tribe
- [ ] "Create Player" button works
- [ ] "Cancel" button closes popup
- [ ] Default name "Player" is used if field is empty

### ✅ **After Player Creation**
- [ ] Status display updates with player name
- [ ] Status display shows selected faction
- [ ] Victory points show as 0
- [ ] All navigation buttons now work (no more "create player" prompts)

---

## 📊 **Player Stats Screen Testing**

### ✅ **Navigation**
- [ ] Screen loads when clicking "👤 Player Stats"
- [ ] Back button returns to main menu
- [ ] Screen fits properly in portrait mode

### ✅ **Player Information Display**
- [ ] Player name displays correctly
- [ ] Faction name shows
- [ ] All stats display with proper values:
  - [ ] HP: Current/Max
  - [ ] Attack Power
  - [ ] Defense
  - [ ] Speed
  - [ ] Accuracy
  - [ ] Critical Hit Chance
  - [ ] Dodge Chance
  - [ ] Parry Chance
  - [ ] Constitution

### ✅ **Equipment Display**
- [ ] Armor section shows equipped items
- [ ] Weapon section shows equipped items
- [ ] Empty slots show "Empty"
- [ ] Equipped items show name correctly

### ✅ **Abilities Display**
- [ ] Shows faction abilities
- [ ] Shows which abilities are in ability slots
- [ ] Ability descriptions display

---

## ⚔️ **Equipment Screen Testing**

### ✅ **Navigation**
- [ ] Screen loads when clicking "⚔️ Equipment"
- [ ] Back button returns to main menu
- [ ] Screen fits properly in portrait mode

### ✅ **Equipment Management**
- [ ] Visual equipment slots display correctly
- [ ] Generate equipment buttons work for each slot
- [ ] Unequip buttons work
- [ ] Equipment popup shows item details
- [ ] Stat bonuses update when equipping/unequipping
- [ ] Equipment images load correctly

### ✅ **Equipment Types**
- [ ] **Armor Slots**: Helmet, Chest, Pants, Boots, Gloves
- [ ] **Weapon Slots**: Main Hand, Off Hand
- [ ] **Armor Types**: Cloth, Leather, Metal
- [ ] **Weapon Types**: Sword, Axe, Bow, Crossbow, Knife, Mace, Hammer, Shield, Staff

---

## 🏛️ **Faction Screen Testing**

### ✅ **Navigation**
- [ ] Screen loads when clicking "🏛️ Faction & Abilities"
- [ ] Back button returns to main menu
- [ ] Screen fits properly in portrait mode

### ✅ **Faction Information**
- [ ] Current faction displays correctly
- [ ] Faction description shows
- [ ] Faction passive ability displays

### ✅ **Ability Management**
- [ ] All 5 faction abilities display
- [ ] Ability descriptions show
- [ ] Ability slot assignment works
- [ ] Only 4 abilities can be selected
- [ ] Ability cycling order displays

### ✅ **Faction Change**
- [ ] "Change Faction" button opens popup
- [ ] All 3 factions available for selection
- [ ] Faction change updates abilities
- [ ] Player stats update with new faction

---

## ⚡ **Combat Screen Testing**

### ✅ **Navigation**
- [ ] Screen loads when clicking "⚡ Duel"
- [ ] Back button returns to main menu
- [ ] Screen fits properly in portrait mode

### ✅ **Combat Setup**
- [ ] "Start Duel" button works
- [ ] Opponent generation works
- [ ] Opponent info popup displays
- [ ] Combat begins automatically

### ✅ **Combat Interface**
- [ ] Turn order displays correctly
- [ ] Player and opponent HP bars show
- [ ] Ability buttons display
- [ ] Combat log shows actions
- [ ] Turn counter works

### ✅ **Combat Mechanics**
- [ ] Abilities cycle through correctly
- [ ] Damage calculations work
- [ ] Critical hits occur
- [ ] Misses/dodges occur
- [ ] Combat ends when HP reaches 0
- [ ] Winner is determined correctly

### ✅ **Combat Results**
- [ ] Victory/defeat message shows
- [ ] Victory points awarded for wins
- [ ] Combat statistics display
- [ ] Return to main menu works

---

## ⚙️ **Settings Screen Testing**

### ✅ **Navigation**
- [ ] Screen loads when clicking "⚙️ Settings"
- [ ] Back button returns to main menu
- [ ] Screen fits properly in portrait mode

### ✅ **Settings Options**
- [ ] Settings options display
- [ ] Any available settings work
- [ ] Screen functions properly

---

## 🎮 **Complete Gameplay Flow Testing**

### ✅ **Full Game Session**
1. [ ] **Create Player**: Choose name and faction
2. [ ] **View Stats**: Check initial stats
3. [ ] **Manage Equipment**: Equip better gear
4. [ ] **Set Abilities**: Choose 4 abilities
5. [ ] **Start Duel**: Fight opponent
6. [ ] **Check Results**: Verify victory points
7. [ ] **Repeat**: Test multiple duels

### ✅ **Edge Cases**
- [ ] **No Player**: All screens prompt for player creation
- [ ] **Empty Ability Slots**: Combat still works
- [ ] **No Equipment**: Player has base stats
- [ ] **Combat Variations**: Different outcomes possible

---

## 📱 **Mobile-Specific Testing**

### ✅ **Touch Interactions**
- [ ] All buttons respond to touch
- [ ] Touch targets are appropriately sized
- [ ] Scrolling works where needed
- [ ] Popups close when touching outside

### ✅ **Screen Orientation**
- [ ] App stays in portrait mode
- [ ] Layout adapts to different screen sizes
- [ ] Text remains readable
- [ ] Buttons remain accessible

### ✅ **Performance**
- [ ] App loads quickly
- [ ] Screen transitions are smooth
- [ ] No lag during combat
- [ ] Memory usage is reasonable

---

## 🐛 **Error Testing**

### ✅ **Error Handling**
- [ ] Invalid inputs are handled gracefully
- [ ] App doesn't crash on edge cases
- [ ] Error messages are user-friendly
- [ ] App recovers from errors

### ✅ **Data Validation**
- [ ] Player names are validated
- [ ] Equipment stats are reasonable
- [ ] Combat calculations are correct
- [ ] Victory points are accurate

---

## ✅ **Final Verification**

### 🎯 **Core Features Working**
- [ ] Player creation and management
- [ ] Equipment system with visual interface
- [ ] Faction abilities and passives
- [ ] Turn-based combat with ability cycling
- [ ] Victory point progression
- [ ] All screens and navigation

### 🎯 **Mobile Optimization**
- [ ] Portrait mode layout
- [ ] Touch-friendly interface
- [ ] Responsive design
- [ ] Smooth performance

### 🎯 **Asset Integration**
- [ ] All images load correctly
- [ ] Equipment icons display
- [ ] Ability icons show
- [ ] UI elements render properly

---

## 🚀 **Ready for Deployment**

If all items above are checked ✅, the mobile app is ready for:

1. **Android Build**: `buildozer android debug`
2. **Device Testing**: Install APK on physical device
3. **Distribution**: Share with testers

## 📝 **Testing Notes**

- Test on different screen sizes if possible
- Verify all touch interactions work
- Check that combat is balanced and fun
- Ensure no functionality is missing
- Document any issues found

**The Idle Duelist mobile app is fully functional and ready for testing!** 🎉




