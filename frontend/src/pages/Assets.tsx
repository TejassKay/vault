import React, { useEffect, useState } from 'react';
import {
  ApplianceResponse,
  BillResponse,
  confirmAppliance,
  fetchAppliances,
  markServiceDone,
  uploadBill,
} from '../api/assets';
import { getLabel } from '../lib/labels.js';
import Money from '../components/Money';
import Card from '../components/Card';
import StatusPill from '../components/StatusPill';

function formatToIsoDate(dStr: string): string {
  if (!dStr) return '';
  const cleaned = dStr.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(cleaned)) return cleaned;
  if (cleaned.includes('/')) {
    const parts = cleaned.split('/');
    if (parts.length === 3) {
      const year = parts[2].length === 2 ? `20${parts[2]}` : parts[2];
      return `${year}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
  }
  const months: Record<string, string> = {
    jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06',
    jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12',
  };
  const match = cleaned.match(/^(\d{1,2})[-\s]([a-zA-Z]{3,9})[-\s](\d{2,4})$/);
  if (match) {
    const day = match[1].padStart(2, '0');
    const monStr = match[2].slice(0, 3).toLowerCase();
    const mon = months[monStr] || '01';
    const year = match[3].length === 2 ? `20${match[3]}` : match[3];
    return `${year}-${mon}-${day}`;
  }
  return '';
}

function calculateWarrantyStatus(endDateStr: string | null | undefined): { label: string; variant: 'growth' | 'liability' | 'neutral' } {
  if (!endDateStr) return { label: 'NO WARRANTY', variant: 'neutral' };
  const end = new Date(endDateStr);
  const now = new Date();
  const diffDays = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return { label: 'WARRANTY EXPIRED', variant: 'liability' };
  }
  if (diffDays <= 30) {
    return { label: `WARRANTY ENDS IN ${diffDays} DAYS`, variant: 'liability' };
  }
  return { label: 'WARRANTY ACTIVE', variant: 'growth' };
}

export const Assets: React.FC = () => {
  const [appliances, setAppliances] = useState<ApplianceResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Upload & Review state
  const [uploading, setUploading] = useState(false);
  const [extractedBill, setExtractedBill] = useState<BillResponse | null>(null);

  // Review Form fields
  const [productName, setProductName] = useState('');
  const [brand, setBrand] = useState('');
  const [modelNumber, setModelNumber] = useState('');
  const [seller, setSeller] = useState('');
  const [price, setPrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');
  const [warrantyMonths, setWarrantyMonths] = useState('12');
  const [categoryId, setCategoryId] = useState('1'); // Default 1 (AC)

  const loadAppliances = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAppliances();
      setAppliances(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load appliances');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppliances();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      const bill = await uploadBill(file);
      setExtractedBill(bill);

      // Pre-fill form from extraction
      const ext = bill.extraction_json || {};
      setProductName(String(ext.product_name?.value || ''));
      setBrand(String(ext.brand?.value || ''));
      setModelNumber(String(ext.model_number?.value || ''));
      setSeller(String(ext.seller?.value || ''));
      setPrice(ext.price?.value ? String(ext.price.value) : '');

      const rawPDate = String(ext.purchase_date?.value || '');
      const isoPDate = formatToIsoDate(rawPDate);
      setPurchaseDate(isoPDate || new Date().toISOString().split('T')[0]);
      setWarrantyMonths(String(ext.warranty_months?.value || '12'));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to upload bill');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!extractedBill) return;

    try {
      setLoading(true);
      setError(null);

      const ext = extractedBill.extraction_json || {};
      const correctedFieldsObj: Record<string, boolean> = {};

      if (productName !== String(ext.product_name?.value || '')) correctedFieldsObj.product_name = true;
      if (brand !== String(ext.brand?.value || '')) correctedFieldsObj.brand = true;
      if (modelNumber !== String(ext.model_number?.value || '')) correctedFieldsObj.model_number = true;
      if (seller !== String(ext.seller?.value || '')) correctedFieldsObj.seller = true;
      if (price !== (ext.price?.value ? String(ext.price.value) : '')) correctedFieldsObj.price = true;
      if (purchaseDate !== String(ext.purchase_date?.value || '')) correctedFieldsObj.purchase_date = true;
      if (warrantyMonths !== String(ext.warranty_months?.value || '')) correctedFieldsObj.warranty_months = true;

      await confirmAppliance({
        bill_id: extractedBill.bill_id,
        category_id: parseInt(categoryId, 10),
        product_name: productName,
        brand: brand || null,
        model_number: modelNumber || null,
        seller: seller || null,
        price: price ? parseFloat(price) : null,
        purchase_date: purchaseDate,
        warranty_months: warrantyMonths ? parseInt(warrantyMonths, 10) : 12,
        corrected_fields: correctedFieldsObj,
      });

      setExtractedBill(null);
      await loadAppliances();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to confirm appliance');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleServiceComplete = async (serviceId: number) => {
    try {
      await markServiceDone(serviceId);
      await loadAppliances();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to update service');
      }
    }
  };

  const renderFieldConf = (fieldName: string) => {
    const f = extractedBill?.extraction_json?.[fieldName];
    if (!f) return null;
    const conf = f.confidence ?? 0.0;
    if (conf < 0.6) {
      return (
        <span className="ml-1.5 inline-flex items-center px-1.5 py-0.2 rounded-sm text-[10px] font-mono text-liability bg-liability/10 border border-liability/30">
          Verify ({(conf * 100).toFixed(0)}%)
        </span>
      );
    }
    return (
      <span className="ml-1.5 text-[11px] font-mono text-muted-ink">
        ({(conf * 100).toFixed(0)}% conf)
      </span>
    );
  };

  const getFieldInputClass = (fieldName: string) => {
    const f = extractedBill?.extraction_json?.[fieldName];
    const conf = f?.confidence ?? 0.0;
    if (conf < 0.6) {
      return 'w-full text-xs font-mono p-2 border border-liability/60 bg-liability/5 rounded-sm focus:border-ink transition-colors';
    }
    return 'w-full text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink transition-colors';
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-serif text-ink tracking-tight">Physical Asset Index</h1>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Archival index cards for household appliances, warranties, and service schedules
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-surface border border-liability text-liability rounded-sm text-xs font-sans">
          {error}
        </div>
      )}

      {/* Bill Upload Section */}
      <Card className="border border-border space-y-4">
        <div>
          <h2 className="text-xl font-serif text-ink">Index New Bill or Invoice</h2>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Supported formats: PDF, JPG, PNG (Max 10MB). Text, prices, serial numbers, and warranty intervals will be parsed into an archival index record.
          </p>
        </div>
        <div className="flex items-center gap-4 pt-1">
          <label className="cursor-pointer bg-ink hover:bg-muted-ink text-canvas font-mono py-2 px-4 rounded-sm text-xs transition-colors border border-ink">
            {uploading ? 'Processing Bill...' : 'Upload Bill / Invoice'}
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              disabled={uploading}
              onChange={handleFileUpload}
            />
          </label>
          {uploading && <span className="text-xs font-mono text-muted-ink">Parsing document fields...</span>}
        </div>
      </Card>

      {/* Extracted Bill Review Form */}
      {extractedBill && (
        <Card className="border border-ink bg-surface space-y-4">
          <div className="flex justify-between items-center border-b border-border pb-3">
            <div>
              <h2 className="text-xl font-serif text-ink">Review & Verify Extracted Ledger Record</h2>
              <p className="text-xs font-sans text-muted-ink mt-0.5">
                Parse Status: <span className="font-mono font-medium text-ink">{getLabel(extractedBill.parse_status)}</span>. Verify or adjust fields before logging to the ledger.
              </p>
            </div>
            <button
              onClick={() => setExtractedBill(null)}
              className="text-xs font-mono text-muted-ink hover:text-ink"
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleConfirm} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Product Name * {renderFieldConf('product_name')}
              </label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                className={getFieldInputClass('product_name')}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Brand {renderFieldConf('brand')}
              </label>
              <input
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                className={getFieldInputClass('brand')}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Model Number {renderFieldConf('model_number')}
              </label>
              <input
                type="text"
                value={modelNumber}
                onChange={(e) => setModelNumber(e.target.value)}
                className={getFieldInputClass('model_number')}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Seller {renderFieldConf('seller')}
              </label>
              <input
                type="text"
                value={seller}
                onChange={(e) => setSeller(e.target.value)}
                className={getFieldInputClass('seller')}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Price (INR) {renderFieldConf('price')}
              </label>
              <input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className={getFieldInputClass('price')}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Purchase Date * {renderFieldConf('purchase_date')}
              </label>
              <input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                className={getFieldInputClass('purchase_date')}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Warranty Period (Months) {renderFieldConf('warranty_months')}
              </label>
              <input
                type="number"
                value={warrantyMonths}
                onChange={(e) => setWarrantyMonths(e.target.value)}
                className={getFieldInputClass('warranty_months')}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-muted-ink mb-1">
                Appliance Category (Service Schedule) {renderFieldConf('category')}
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className={getFieldInputClass('category')}
              >
                <option value="1">Air Conditioner (6mo interval)</option>
                <option value="2">Refrigerator (12mo interval)</option>
                <option value="3">Washing Machine (12mo interval)</option>
                <option value="4">Water Purifier / RO (6mo interval)</option>
                <option value="5">Geyser (12mo interval)</option>
                <option value="6">Chimney (6mo interval)</option>
              </select>
            </div>

            <div className="md:col-span-2 flex justify-end gap-3 mt-2 pt-3 border-t border-border">
              <button
                type="submit"
                disabled={loading}
                className="bg-growth hover:bg-growth/90 text-surface font-mono py-2 px-5 rounded-sm text-xs transition-colors"
              >
                Confirm & Log to Ledger
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* Appliances Archival Index Cards */}
      <div className="space-y-4">
        <div className="flex justify-between items-center border-b border-border pb-3">
          <h2 className="text-xl font-serif text-ink">Archival Index Cards ({appliances.length})</h2>
          <button
            onClick={loadAppliances}
            className="text-xs font-mono text-muted-ink hover:text-ink"
          >
            Refresh
          </button>
        </div>

        {loading && appliances.length === 0 ? (
          <Card className="text-center py-12 text-xs font-mono text-muted-ink">
            Loading archival index cards...
          </Card>
        ) : appliances.length === 0 ? (
          <Card className="text-center py-12 text-xs font-sans text-muted-ink">
            No appliances registered in the index. Upload a bill above to record purchases, warranties, and maintenance.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {appliances.map((appliance) => {
              const statusInfo = calculateWarrantyStatus(appliance.warranty_end_date);
              return (
                <Card
                  key={appliance.appliance_id}
                  className="border border-border bg-surface flex flex-col justify-between space-y-4 hover:border-ink transition-colors"
                >
                  <div>
                    {/* Header: Title + Status Pill */}
                    <div className="flex items-start justify-between gap-3 border-b border-border pb-3">
                      <div>
                        <span className="text-[10px] font-mono tracking-wider uppercase text-muted-ink block">
                          Card #{appliance.appliance_id} • {appliance.brand || 'Appliance'}
                        </span>
                        <h3 className="text-lg font-serif text-ink mt-0.5 leading-snug">
                          {appliance.product_name}
                        </h3>
                      </div>
                      <StatusPill
                        label={statusInfo.label}
                        variant={statusInfo.variant}
                      />
                    </div>

                    {/* Meta Fields: Mono Model, Purchase Date, Price */}
                    <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                      {appliance.model_number && (
                        <div className="col-span-2 bg-canvas px-2.5 py-1.5 rounded-sm border border-border flex items-center justify-between">
                          <span className="text-muted-ink text-[11px] font-sans">Model / Serial No:</span>
                          <span className="font-mono text-ink font-medium select-all">
                            {appliance.model_number}
                          </span>
                        </div>
                      )}

                      <div className="bg-canvas px-2.5 py-1.5 rounded-sm border border-border">
                        <span className="text-muted-ink text-[10px] font-sans block uppercase">Purchased</span>
                        <span className="font-mono text-xs text-ink">{appliance.purchase_date}</span>
                      </div>

                      <div className="bg-canvas px-2.5 py-1.5 rounded-sm border border-border">
                        <span className="text-muted-ink text-[10px] font-sans block uppercase">Invoice Price</span>
                        <div className="font-mono text-xs text-ink">
                          {appliance.price ? <Money amount={appliance.price} /> : '—'}
                        </div>
                      </div>

                      {appliance.seller && (
                        <div className="col-span-2 text-[11px] font-sans text-muted-ink px-1">
                          Seller: <span className="text-ink font-medium">{appliance.seller}</span>
                        </div>
                      )}
                    </div>

                    {/* Services Schedule */}
                    {appliance.services && appliance.services.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-border space-y-2">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                          Service Schedule ({appliance.services.length})
                        </span>
                        <div className="space-y-1.5">
                          {appliance.services.map((svc) => (
                            <div
                              key={svc.service_id}
                              className="bg-canvas p-2 rounded-sm border border-border text-xs flex justify-between items-center"
                            >
                              <div>
                                <span className="font-mono text-[11px] text-ink block">
                                  Due: {svc.due_date}
                                </span>
                                <span className="text-muted-ink text-[10px] font-sans">
                                  {svc.guidance_label === 'general' ? 'General Guidance' : 'Manufacturer-Confirmed'}
                                </span>
                              </div>
                              <div>
                                {svc.status === 'done' ? (
                                  <StatusPill label="COMPLETED" variant="growth" />
                                ) : (
                                  <button
                                    onClick={() => handleServiceComplete(svc.service_id)}
                                    className="px-2.5 py-1 bg-surface hover:bg-canvas text-ink border border-border rounded-sm text-[11px] font-mono transition-colors"
                                  >
                                    Mark Done
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] font-mono text-muted-ink">
                    <span>Warranty: {appliance.warranty_end_date || 'N/A'}</span>
                    <span>ID: {appliance.appliance_id}</span>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Assets;
