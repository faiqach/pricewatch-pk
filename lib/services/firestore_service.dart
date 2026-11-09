import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreService {
  FirestoreService({FirebaseFirestore? firestore})
      : _providedFirestore = firestore;

  final FirebaseFirestore? _providedFirestore;
  FirebaseFirestore get _firestore => _providedFirestore ?? FirebaseFirestore.instance;

  Stream<List<Map<String, dynamic>>> watchCrops({
    int limit = 0,
    String? orderByField = 'name',
    bool descending = false,
  }) {
    return _watchCollection(
      collectionPath: 'crops',
      limit: limit,
      orderByField: orderByField,
      descending: descending,
    );
  }

  /// Streams [watchCrops] merged with the `market_prices` collection
  /// (vendor/open-market prices), joined by crop name. Each emitted map
  /// carries the official price as `price` and the matched vendor price
  /// as `vendorPrice` (falling back to the official price if no vendor
  /// record exists yet for that crop).
  Stream<List<Map<String, dynamic>>> watchCropsCombined({
    int limit = 0,
    String? orderByField = 'name',
    bool descending = false,
  }) {
    late StreamController<List<Map<String, dynamic>>> controller;
    StreamSubscription? officialSub;
    StreamSubscription? vendorSub;
    List<Map<String, dynamic>> latestOfficial = [];
    List<Map<String, dynamic>> latestVendor = [];

    void emit() {
      final Map<String, Map<String, dynamic>> vendorByName = {
        for (final v in latestVendor)
          (v['name'] as String? ?? '').toLowerCase(): v,
      };

      final merged = latestOfficial.map((official) {
        final String key = (official['name'] as String? ?? '').toLowerCase();
        final vendor = vendorByName[key];
        return {
          ...official,
          'vendorPrice': (vendor?['price'] as num?)?.toDouble() ?? official['price'],
        };
      }).toList();

      controller.add(merged);
    }

    controller = StreamController<List<Map<String, dynamic>>>.broadcast(
      onListen: () {
        officialSub = watchCrops(
          limit: limit,
          orderByField: orderByField,
          descending: descending,
        ).listen((data) {
          latestOfficial = data;
          emit();
        });
        vendorSub = _watchCollection(collectionPath: 'market_prices').listen((data) {
          latestVendor = data;
          emit();
        });
      },
      onCancel: () {
        officialSub?.cancel();
        vendorSub?.cancel();
      },
    );

    return controller.stream;
  }

  Stream<List<Map<String, dynamic>>> watchMandis({int limit = 0}) {
    return _watchCollection(
      collectionPath: 'mandis',
      limit: limit,
      orderByField: 'name',
    );
  }

  Stream<List<Map<String, dynamic>>> watchNews({int limit = 0}) {
    return _watchCollection(
      collectionPath: 'news',
      limit: limit,
      orderByField: 'date',
      descending: true,
    );
  }

  Stream<List<Map<String, dynamic>>> _watchCollection({
    required String collectionPath,
    int limit = 0,
    String? orderByField,
    bool descending = false,
  }) {
    Query<Map<String, dynamic>> query = _firestore.collection(collectionPath);

    if (orderByField != null) {
      query = query.orderBy(orderByField, descending: descending);
    }

    if (limit > 0) {
      query = query.limit(limit);
    }

    return query.snapshots().map(
          (snapshot) => snapshot.docs
              .map((doc) => _normalizeDoc(doc.id, doc.data()))
              .toList(),
        );
  }

  Map<String, dynamic> _normalizeDoc(
    String docId,
    Map<String, dynamic> data,
  ) {
    final Map<String, dynamic> copy = Map<String, dynamic>.from(data);

    if (!copy.containsKey('id')) {
      final int? parsedId = int.tryParse(docId);
      copy['id'] = parsedId ?? 0;
    }

    copy['docId'] = docId;
    return copy;
  }

  Stream<List<Map<String, dynamic>>> watchCropHistory(String cropId) {
    return _firestore
        .collection('crops')
        .doc(cropId)
        .collection('history')
        .orderBy('date', descending: false)
        .snapshots()
        .map((snap) => snap.docs.map((doc) => doc.data()).toList());
  }

  Future<void> seedInitialData(List<Map<String, dynamic>> dummyCrops, Map<String, List<Map<String, dynamic>>> cropHistory) async {
    final cropsCol = _firestore.collection('crops');
    final snap = await cropsCol.limit(1).get();
    if (snap.docs.isNotEmpty) {
      return; // Already seeded
    }

    final batch = _firestore.batch();
    for (var crop in dummyCrops) {
      final docRef = cropsCol.doc(crop['name']);
      batch.set(docRef, {
        ...crop,
        'docId': crop['name'],
        'updatedAt': FieldValue.serverTimestamp(),
      });

      final history = cropHistory[crop['name']] ?? [];
      for (var entry in history) {
        final historyRef = docRef.collection('history').doc(entry['date']);
        batch.set(historyRef, {
          'date': entry['date'],
          'price': entry['price'],
        });
      }
    }
    await batch.commit();
  }
}

