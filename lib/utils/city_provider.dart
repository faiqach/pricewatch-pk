import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ─────────────────────────────────────────────────────────────────────────────
// CityProvider  –  InheritedNotifier-based city selector (mirrors LanguageProvider)
//   • Persists the chosen city to device preferences via shared_preferences
//   • Drives session-wide filtering: any screen reading CityScope.of(context)
//     rebuilds automatically when the city changes
// ─────────────────────────────────────────────────────────────────────────────

class CityNotifier extends ChangeNotifier {
  static const List<String> availableCities = [
    'Bahawalnagar',
    'Lahore',
    'Multan',
    'Bahawalpur',
    'Islamabad',
  ];

  static const String defaultCity = 'Lahore';
  static const String _prefsKey = 'selected_city';

  String _city = defaultCity;
  String get city => _city;

  /// Loads the previously saved city from device preferences, if any.
  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefsKey);
    if (saved != null && availableCities.contains(saved) && saved != _city) {
      _city = saved;
      notifyListeners();
    }
  }

  Future<void> setCity(String city) async {
    if (!availableCities.contains(city) || city == _city) return;
    _city = city;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, city);
  }
}

/// Put this above MaterialApp in main.dart:
///   CityScope(child: MaterialApp(...))
class CityScope extends StatefulWidget {
  final Widget child;
  const CityScope({super.key, required this.child});

  @override
  State<CityScope> createState() => _CityScopeState();

  static final CityNotifier _fallback = CityNotifier();

  static CityNotifier of(BuildContext context) {
    final inherited = context.dependOnInheritedWidgetOfExactType<_CityInherited>();
    return inherited?.notifier ?? _fallback;
  }
}

class _CityScopeState extends State<CityScope> {
  final CityNotifier _notifier = CityNotifier();

  @override
  void initState() {
    super.initState();
    _notifier.load();
  }

  @override
  void dispose() {
    _notifier.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _notifier,
      builder: (context, child) => _CityInherited(
        notifier: _notifier,
        child: widget.child,
      ),
    );
  }
}

class _CityInherited extends InheritedNotifier<CityNotifier> {
  const _CityInherited({
    required super.notifier,
    required super.child,
  });
}
