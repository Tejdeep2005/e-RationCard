import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { LogOut, CheckCircle, XCircle, Trash2, Send, Users } from 'lucide-react';

const AdminDashboard = ({ user, onLogout }) => {
  const [cards, setCards] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [tokenData, setTokenData] = useState({
    message: '',
    time_slot: ''
  });
  const [showTokenDialog, setShowTokenDialog] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [cardsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/cards`),
        axios.get(`${API}/admin/users`)
      ]);
      setCards(cardsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (cardId) => {
    try {
      const response = await axios.put(`${API}/admin/cards/${cardId}/approve`);
      toast.success(`Card approved! Card Number: ${response.data.card_number}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to approve card');
    }
  };

  const handleReject = async (cardId) => {
    try {
      await axios.put(`${API}/admin/cards/${cardId}/reject`);
      toast.success('Card rejected');
      fetchData();
    } catch (error) {
      toast.error('Failed to reject card');
    }
  };

  const handleDelete = async (cardId) => {
    if (window.confirm('Are you sure you want to delete this card?')) {
      try {
        await axios.delete(`${API}/admin/cards/${cardId}`);
        toast.success('Card deleted');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete card');
      }
    }
  };

  const handleUserSelect = (userId) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const handleDistributeTokens = async () => {
    if (selectedUsers.length === 0) {
      toast.error('Please select at least one user');
      return;
    }

    if (selectedUsers.length > 50) {
      toast.error('Maximum 50 users can be selected');
      return;
    }

    try {
      const response = await axios.post(`${API}/admin/distribute-tokens`, {
        user_ids: selectedUsers,
        message: tokenData.message,
        time_slot: tokenData.time_slot
      });
      toast.success(response.data.message);
      setShowTokenDialog(false);
      setSelectedUsers([]);
      setTokenData({ message: '', time_slot: '' });
    } catch (error) {
      toast.error('Failed to distribute tokens');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: 'secondary',
      approved: 'default',
      rejected: 'destructive',
      fake: 'destructive'
    };
    return <Badge variant={variants[status] || 'secondary'}>{status.toUpperCase()}</Badge>;
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <div className="container mx-auto px-4 py-8" data-testid="admin-dashboard">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 bg-white/10 backdrop-blur-lg p-6 rounded-2xl border border-white/20">
          <div>
            <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Admin Dashboard</h1>
            <p className="text-white/80">Welcome, {user.name}</p>
          </div>
          <Button variant="secondary" onClick={onLogout} data-testid="admin-logout-btn">
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="cards" className="space-y-6">
          <TabsList className="bg-white/10 backdrop-blur-lg border border-white/20" data-testid="admin-tabs">
            <TabsTrigger value="cards" data-testid="cards-tab">Ration Cards</TabsTrigger>
            <TabsTrigger value="tokens" data-testid="tokens-tab">Token Distribution</TabsTrigger>
          </TabsList>

          <TabsContent value="cards">
            <Card className="backdrop-blur-xl bg-white/95 shadow-2xl border-0">
              <CardHeader>
                <CardTitle>All Ration Cards</CardTitle>
                <CardDescription>Manage ration card applications</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-purple-600"></div>
                  </div>
                ) : cards.length === 0 ? (
                  <p className="text-center py-8 text-gray-500" data-testid="no-cards-message">No ration cards found</p>
                ) : (
                  <div className="space-y-4" data-testid="cards-list">
                    {cards.map((card) => (
                      <div key={card.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors" data-testid={`card-item-${card.id}`}>
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-bold text-lg">{card.name}</h3>
                            <p className="text-sm text-gray-600">Aadhaar: {card.aadhaar}</p>
                            {card.card_number && <p className="text-sm font-semibold text-purple-600">Card: {card.card_number}</p>}
                          </div>
                          <div>{getStatusBadge(card.status)}</div>
                        </div>
                        <div className="grid md:grid-cols-2 gap-2 text-sm mb-3">
                          <p><span className="font-semibold">Address:</span> {card.address}</p>
                          <p><span className="font-semibold">Family:</span> {card.family_members} members</p>
                        </div>
                        {card.ai_verification_result && (
                          <div className="bg-blue-50 p-3 rounded text-sm mb-3">
                            <p className="font-semibold text-blue-800">AI Verification:</p>
                            <p className="text-blue-700">{card.ai_verification_result}</p>
                          </div>
                        )}
                        <div className="flex gap-2">
                          {card.status === 'pending' && (
                            <>
                              <Button size="sm" onClick={() => handleApprove(card.id)} data-testid={`approve-btn-${card.id}`}>
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Approve
                              </Button>
                              <Button size="sm" variant="destructive" onClick={() => handleReject(card.id)} data-testid={`reject-btn-${card.id}`}>
                                <XCircle className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          <Button size="sm" variant="outline" onClick={() => handleDelete(card.id)} data-testid={`delete-btn-${card.id}`}>
                            <Trash2 className="w-4 h-4 mr-1" />
                            Delete
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tokens">
            <Card className="backdrop-blur-xl bg-white/95 shadow-2xl border-0">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Token Distribution</CardTitle>
                    <CardDescription>Send SMS tokens to users (Max 50)</CardDescription>
                  </div>
                  <Dialog open={showTokenDialog} onOpenChange={setShowTokenDialog}>
                    <DialogTrigger asChild>
                      <Button disabled={selectedUsers.length === 0} data-testid="distribute-tokens-btn">
                        <Send className="w-4 h-4 mr-2" />
                        Send Tokens ({selectedUsers.length})
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Distribute SMS Tokens</DialogTitle>
                        <DialogDescription>Send tokens to {selectedUsers.length} selected users</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="message">Message</Label>
                          <Input
                            id="message"
                            placeholder="Your token for ration collection"
                            value={tokenData.message}
                            onChange={(e) => setTokenData({ ...tokenData, message: e.target.value })}
                            data-testid="token-message-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="time_slot">Time Slot</Label>
                          <Input
                            id="time_slot"
                            placeholder="10:00 AM - 12:00 PM"
                            value={tokenData.time_slot}
                            onChange={(e) => setTokenData({ ...tokenData, time_slot: e.target.value })}
                            data-testid="token-timeslot-input"
                          />
                        </div>
                        <Button onClick={handleDistributeTokens} className="w-full" data-testid="send-tokens-btn">
                          Send Tokens
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-purple-600"></div>
                  </div>
                ) : users.length === 0 ? (
                  <p className="text-center py-8 text-gray-500" data-testid="no-users-message">No users found</p>
                ) : (
                  <div className="space-y-3" data-testid="users-list">
                    {users.map((u) => (
                      <div
                        key={u.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          selectedUsers.includes(u.id) ? 'bg-purple-50 border-purple-500' : 'hover:bg-gray-50'
                        }`}
                        onClick={() => handleUserSelect(u.id)}
                        data-testid={`user-item-${u.id}`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold">{u.name}</h3>
                            <p className="text-sm text-gray-600">{u.email}</p>
                            <p className="text-sm text-gray-600">{u.phone}</p>
                          </div>
                          <div className="flex items-center">
                            <input
                              type="checkbox"
                              checked={selectedUsers.includes(u.id)}
                              onChange={() => handleUserSelect(u.id)}
                              className="w-5 h-5"
                              data-testid={`user-checkbox-${u.id}`}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;